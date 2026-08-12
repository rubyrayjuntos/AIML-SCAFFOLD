from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from platform_core.contracts.artifact_uri import validate_artifact_uri
from platform_core.contracts.evidence import (
    ArtifactReference,
    EvidenceState,
    OperationReceipt,
    create_evidence_event,
)
from platform_core.evidence.blob_sink import BlobEvidenceSink, EvidenceConflictError
from platform_core.evidence.projector import project_operations

NOW = datetime(2026, 8, 11, 12, 0, tzinfo=UTC)


def event(
    sequence: int,
    state: EvidenceState,
    *,
    occurred_at: datetime = NOW,
    metadata=None,
    operation_id: str = "op-1",
    capability: str = "ml",
    source_run_id: str = "run-1",
    project: str = "example-risk",
    environment: str = "dev",
    artifact_references=(),
):
    return create_evidence_event(
        operation_id=operation_id,
        project=project,
        environment=environment,
        provider="azure_ml",
        capability=capability,
        operation="training",
        state=state,
        source_run_id=source_run_id,
        source_sequence=sequence,
        occurred_at=occurred_at,
        artifact_references=artifact_references,
        metadata=metadata,
    )


class FakeDownload:
    def __init__(self, value: bytes) -> None:
        self.value = value

    def readall(self) -> bytes:
        return self.value


class FakeBlob:
    def __init__(self, store: dict[str, bytes], name: str) -> None:
        self.store = store
        self.name = name

    def upload_blob(self, value: bytes, *, overwrite: bool) -> None:
        assert overwrite is False
        if self.name in self.store:
            raise RuntimeError("exists")
        self.store[self.name] = value

    def download_blob(self) -> FakeDownload:
        return FakeDownload(self.store[self.name])


class FakeContainer:
    def __init__(self) -> None:
        self.store: dict[str, bytes] = {}

    def get_blob_client(self, name: str) -> FakeBlob:
        return FakeBlob(self.store, name)


def test_event_identity_and_payload_are_deterministic() -> None:
    assert event(0, EvidenceState.STARTED) == event(0, EvidenceState.STARTED)
    assert event(0, EvidenceState.STARTED).blob_name.startswith(
        "v1/example-risk/dev/2026/08/11/op-1/sha256:"
    )
    assert event(0, EvidenceState.STARTED).event_identity_version == "1.0"
    assert event(0, EvidenceState.STARTED, capability="registry").event_id != event(
        0, EvidenceState.STARTED
    ).event_id
    assert event(0, EvidenceState.STARTED, operation_id="op-2").event_id != event(
        0, EvidenceState.STARTED
    ).event_id


def test_platform_artifact_uri_validator_uses_generated_conformance_vectors() -> None:
    vectors_path = Path(
        "src/aiml_scaffold/templates/azure_ml_batch/platform/artifact-uri-conformance.json"
    )
    vectors = json.loads(vectors_path.read_text(encoding="utf-8"))
    for uri in vectors["valid"]:
        assert validate_artifact_uri(uri) == uri
        assert ArtifactReference(kind="test", uri=uri).uri == uri
    for uri in vectors["invalid"]:
        with pytest.raises(ValueError, match="artifact URI"):
            validate_artifact_uri(uri)


def test_artifact_reference_error_does_not_echo_rejected_uri() -> None:
    rejected = "https://account.blob.core.windows.net/container/file?sig=do-not-log"
    with pytest.raises(ValueError) as error:
        ArtifactReference(kind="model", uri=rejected)
    assert rejected not in str(error.value)
    assert "do-not-log" not in str(error.value)


def test_sensitive_metadata_is_rejected() -> None:
    with pytest.raises(ValueError, match="sensitive"):
        event(0, EvidenceState.STARTED, metadata={"access_token": "bad"})


def test_blob_sink_is_idempotent_and_conflict_safe() -> None:
    container = FakeContainer()
    sink = BlobEvidenceSink(container)
    first = event(0, EvidenceState.STARTED)
    assert sink.append(first) == "created"
    assert sink.append(first) == "existing"
    container.store[first.blob_name] = json.dumps({"changed": True}).encode()
    with pytest.raises(EvidenceConflictError):
        sink.append(first)


def test_projection_reconciles_late_arrival_and_requires_receipt() -> None:
    started = event(0, EvidenceState.STARTED, occurred_at=NOW)
    running_late = event(1, EvidenceState.RUNNING, occurred_at=NOW + timedelta(minutes=1))
    succeeded = event(2, EvidenceState.SUCCEEDED, occurred_at=NOW + timedelta(minutes=2))
    without_receipt = project_operations([succeeded, running_late, started])
    assert without_receipt["operations"][0]["state"] == "succeeded"
    assert without_receipt["operations"][0]["projection_status"] == "incomplete"
    assert without_receipt["operations"][0]["complete"] is False
    receipt = OperationReceipt(
        project="example-risk",
        environment="dev",
        operation_id="op-1",
        terminal_event_id=succeeded.event_id,
        state=EvidenceState.SUCCEEDED,
    )
    projected = project_operations([succeeded, started, running_late], [receipt])
    assert projected["operations"][0]["complete"] is True
    assert projected["operations"][0]["projection_status"] == "complete"
    assert projected["operations"][0]["errors"] == []


def test_projection_marks_post_terminal_event_invalid() -> None:
    projected = project_operations(
        [
            event(0, EvidenceState.STARTED),
            event(1, EvidenceState.SUCCEEDED),
            event(2, EvidenceState.RUNNING),
        ]
    )["operations"][0]
    assert projected["integrity"] == "invalid"
    assert projected["projection_status"] == "invalid"
    assert projected["complete"] is False
    assert {error["code"] for error in projected["errors"]} == {"POST_TERMINAL_EVENT"}


def test_projection_never_selects_between_conflicting_terminals() -> None:
    projected = project_operations(
        [
            event(0, EvidenceState.STARTED),
            event(1, EvidenceState.SUCCEEDED),
            event(2, EvidenceState.FAILED),
        ]
    )["operations"][0]
    assert projected["projection_status"] == "invalid"
    assert "CONFLICTING_TERMINAL_STATE" in {
        error["code"] for error in projected["errors"]
    }


def test_projection_rejects_distinct_terminal_ids_even_with_same_state() -> None:
    projected = project_operations(
        [
            event(0, EvidenceState.STARTED),
            event(1, EvidenceState.SUCCEEDED),
            event(2, EvidenceState.SUCCEEDED),
        ]
    )["operations"][0]
    assert "CONFLICTING_TERMINAL_STATE" in {
        error["code"] for error in projected["errors"]
    }


@pytest.mark.parametrize(
    "first,second",
    [
        ({"decision": "pass"}, {"decision": "fail"}),
        ({"metric": 0.9}, {"metric": 0.8}),
    ],
)
def test_projection_rejects_terminal_payload_conflicts(
    first: dict, second: dict
) -> None:
    projected = project_operations(
        [
            event(0, EvidenceState.STARTED),
            event(1, EvidenceState.SUCCEEDED, metadata=first),
            event(1, EvidenceState.SUCCEEDED, metadata=second),
        ]
    )["operations"][0]
    codes = {error["code"] for error in projected["errors"]}
    assert {"SEQUENCE_REUSE", "EVENT_ID_CONTENT_CONFLICT"}.issubset(codes)


def test_projection_rejects_terminal_artifact_conflicts() -> None:
    first = (ArtifactReference(kind="model", uri="azureml://models/risk/1"),)
    second = (ArtifactReference(kind="model", uri="azureml://models/risk/2"),)
    projected = project_operations(
        [
            event(0, EvidenceState.STARTED),
            event(1, EvidenceState.SUCCEEDED, artifact_references=first),
            event(1, EvidenceState.SUCCEEDED, artifact_references=second),
        ]
    )["operations"][0]
    codes = {error["code"] for error in projected["errors"]}
    assert {"SEQUENCE_REUSE", "EVENT_ID_CONTENT_CONFLICT"}.issubset(codes)


def test_projection_rejects_sequence_reuse_with_different_content() -> None:
    projected = project_operations(
        [
            event(0, EvidenceState.STARTED),
            event(1, EvidenceState.RUNNING),
            event(1, EvidenceState.SUCCEEDED),
        ]
    )["operations"][0]
    codes = {error["code"] for error in projected["errors"]}
    assert {"SEQUENCE_REUSE", "EVENT_ID_CONTENT_CONFLICT"}.issubset(codes)


def test_projection_marks_skipped_after_failed_invalid() -> None:
    projected = project_operations(
        [
            event(0, EvidenceState.STARTED),
            event(1, EvidenceState.FAILED),
            event(2, EvidenceState.SKIPPED),
        ]
    )["operations"][0]
    assert "CONFLICTING_TERMINAL_STATE" in {
        error["code"] for error in projected["errors"]
    }


def test_projection_marks_missing_start_invalid() -> None:
    projected = project_operations([event(0, EvidenceState.RUNNING)])["operations"][0]
    assert projected["projection_status"] == "invalid"
    assert projected["errors"][0]["code"] == "MISSING_START_STATE"


def test_projection_marks_invalid_transition_and_context() -> None:
    projected = project_operations(
        [
            event(0, EvidenceState.STARTED),
            event(1, EvidenceState.STARTED, source_run_id="other-run"),
        ]
    )["operations"][0]
    codes = {error["code"] for error in projected["errors"]}
    assert {"CONTEXT_MISMATCH", "INVALID_STATE_TRANSITION"}.issubset(codes)


def test_projection_deduplicates_identical_events() -> None:
    started = event(0, EvidenceState.STARTED)
    projected = project_operations([started, started])["operations"][0]
    assert projected["integrity"] == "valid"
    assert projected["projection_status"] == "incomplete"
    assert projected["event_count"] == 1


def test_projection_marks_receipt_mismatch_invalid() -> None:
    started = event(0, EvidenceState.STARTED)
    succeeded = event(1, EvidenceState.SUCCEEDED)
    receipt = OperationReceipt(
        project="example-risk",
        environment="dev",
        operation_id="op-1",
        terminal_event_id=started.event_id,
        state=EvidenceState.SUCCEEDED,
    )
    projected = project_operations([started, succeeded], [receipt])["operations"][0]
    assert projected["projection_status"] == "invalid"
    assert "RECEIPT_MISMATCH" in {error["code"] for error in projected["errors"]}


def test_projection_rejects_receipt_artifacts_that_differ_from_terminal() -> None:
    artifacts = (ArtifactReference(kind="model", uri="azureml://models/risk/1"),)
    started = event(0, EvidenceState.STARTED)
    succeeded = event(1, EvidenceState.SUCCEEDED, artifact_references=artifacts)
    receipt = OperationReceipt(
        project="example-risk",
        environment="dev",
        operation_id="op-1",
        terminal_event_id=succeeded.event_id,
        state=EvidenceState.SUCCEEDED,
        artifact_references=(
            ArtifactReference(kind="model", uri="azureml://models/risk/2"),
        ),
    )
    projected = project_operations([started, succeeded], [receipt])["operations"][0]
    assert "RECEIPT_MISMATCH" in {error["code"] for error in projected["errors"]}


def test_projection_groups_same_operation_id_by_project_and_environment() -> None:
    projected = project_operations(
        [
            event(0, EvidenceState.STARTED, project="product-a"),
            event(0, EvidenceState.STARTED, project="product-b"),
            event(0, EvidenceState.STARTED, environment="test"),
        ]
    )
    assert projected["operation_count"] == 3
    assert {
        (operation["project"], operation["environment"], operation["operation_id"])
        for operation in projected["operations"]
    } == {
        ("product-a", "dev", "op-1"),
        ("product-b", "dev", "op-1"),
        ("example-risk", "test", "op-1"),
    }


def test_projection_rejects_duplicate_and_conflicting_receipts() -> None:
    started = event(0, EvidenceState.STARTED)
    succeeded = event(1, EvidenceState.SUCCEEDED)
    receipt = OperationReceipt(
        project="example-risk",
        environment="dev",
        operation_id="op-1",
        terminal_event_id=succeeded.event_id,
        state=EvidenceState.SUCCEEDED,
    )
    duplicate = project_operations([started, succeeded], [receipt, receipt])["operations"][0]
    assert "DUPLICATE_RECEIPT" in {error["code"] for error in duplicate["errors"]}
    conflicting = receipt.model_copy(update={"state": EvidenceState.FAILED})
    conflict = project_operations([started, succeeded], [receipt, conflicting])["operations"][0]
    assert "CONFLICTING_RECEIPT" in {error["code"] for error in conflict["errors"]}
    assert conflict["complete"] is False


def test_receipts_use_composite_project_environment_operation_identity() -> None:
    events = [
        event(0, EvidenceState.STARTED, project="product-a"),
        event(1, EvidenceState.SUCCEEDED, project="product-a"),
        event(0, EvidenceState.STARTED, project="product-b"),
        event(1, EvidenceState.FAILED, project="product-b"),
    ]
    receipts = [
        OperationReceipt(
            project=item.project,
            environment=item.environment,
            operation_id=item.operation_id,
            terminal_event_id=item.event_id,
            state=item.state,
        )
        for item in (events[1], events[3])
    ]
    projected = project_operations(reversed(events), reversed(receipts))
    assert projected["operation_count"] == 2
    assert all(operation["complete"] for operation in projected["operations"])


def test_projection_is_independent_of_event_and_receipt_iterable_order() -> None:
    started = event(0, EvidenceState.STARTED)
    running = event(1, EvidenceState.RUNNING)
    succeeded = event(2, EvidenceState.SUCCEEDED)
    receipt = OperationReceipt(
        project=succeeded.project,
        environment=succeeded.environment,
        operation_id=succeeded.operation_id,
        terminal_event_id=succeeded.event_id,
        state=succeeded.state,
    )
    forward = project_operations([started, running, succeeded], [receipt])
    reverse = project_operations([succeeded, running, started], [receipt])
    assert forward == reverse


def test_receipt_rejects_non_terminal_state() -> None:
    with pytest.raises(ValueError, match="terminal"):
        OperationReceipt(
            project="example-risk",
            environment="dev",
            operation_id="op",
            terminal_event_id="event",
            state="running",
        )
