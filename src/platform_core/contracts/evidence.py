from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from platform_core.contracts.artifact_uri import validate_artifact_uri


class EvidenceState(StrEnum):
    STARTED = "started"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED = "skipped"


EVENT_IDENTITY_VERSION = "1.0"
EVENT_IDENTITY_FIELDS = (
    "project",
    "environment",
    "provider",
    "capability",
    "operation",
    "operation_id",
    "source_run_id",
    "source_sequence",
)
TERMINAL_STATES = {EvidenceState.SUCCEEDED, EvidenceState.FAILED, EvidenceState.SKIPPED}
_SENSITIVE_KEY_PARTS = (
    "secret",
    "password",
    "token",
    "credential",
    "connection_string",
    "raw_data",
    "prompt",
    "inference_payload",
)


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256(value: str) -> str:
    return f"sha256:{hashlib.sha256(value.encode('utf-8')).hexdigest()}"


def _reject_sensitive_keys(value: Any, path: str = "metadata") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            normalized = str(key).lower()
            if any(part in normalized for part in _SENSITIVE_KEY_PARTS):
                raise ValueError(f"sensitive evidence field is not allowed: {path}.{key}")
            _reject_sensitive_keys(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _reject_sensitive_keys(item, f"{path}[{index}]")


class ArtifactReference(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    kind: str = Field(min_length=1)
    uri: str = Field(min_length=1)
    digest: str | None = Field(default=None, pattern=r"^sha256:[0-9a-f]{64}$")
    version: str | None = None

    @field_validator("uri")
    @classmethod
    def canonical_unsigned_uri(cls, value: str) -> str:
        return validate_artifact_uri(value)


class EvidenceEvent(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "1.0"
    event_identity_version: str = EVENT_IDENTITY_VERSION
    event_id: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    operation_id: str = Field(min_length=1)
    project: str = Field(min_length=1)
    environment: str = Field(min_length=1)
    provider: str = Field(min_length=1)
    capability: str = Field(min_length=1)
    operation: str = Field(min_length=1)
    state: EvidenceState
    source_run_id: str = Field(min_length=1)
    source_sequence: int = Field(ge=0)
    occurred_at: datetime
    recorded_at: datetime
    artifact_references: tuple[ArtifactReference, ...] = ()
    payload_digest: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_event(self) -> EvidenceEvent:
        if self.schema_version != "1.0":
            raise ValueError("unsupported evidence schema_version")
        if self.event_identity_version != EVENT_IDENTITY_VERSION:
            raise ValueError("unsupported event_identity_version")
        _reject_sensitive_keys(self.metadata)
        expected_id = deterministic_event_id(
            project=self.project,
            environment=self.environment,
            provider=self.provider,
            capability=self.capability,
            operation=self.operation,
            operation_id=self.operation_id,
            source_run_id=self.source_run_id,
            source_sequence=self.source_sequence,
        )
        if self.event_id != expected_id:
            raise ValueError("event_id does not match the deterministic event identity")
        expected_digest = evidence_payload_digest(self)
        if self.payload_digest != expected_digest:
            raise ValueError("payload_digest does not match event content")
        return self

    def canonical_json(self) -> str:
        return _canonical_json(self.model_dump(mode="json"))

    @property
    def blob_name(self) -> str:
        date = self.occurred_at.astimezone(UTC)
        return (
            f"v1/{self.project}/{self.environment}/{date:%Y/%m/%d}/"
            f"{self.operation_id}/{self.event_id}.json"
        )


class OperationReceipt(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "1.0"
    project: str = Field(min_length=1)
    environment: str = Field(min_length=1)
    operation_id: str
    terminal_event_id: str
    state: EvidenceState
    artifact_references: tuple[ArtifactReference, ...] = ()

    @model_validator(mode="after")
    def terminal_only(self) -> OperationReceipt:
        if self.state not in TERMINAL_STATES:
            raise ValueError("operation receipt requires a terminal state")
        return self

    @property
    def operation_key(self) -> tuple[str, str, str]:
        return (self.project, self.environment, self.operation_id)


def deterministic_event_id(
    *,
    project: str,
    environment: str,
    provider: str,
    capability: str,
    operation: str,
    operation_id: str,
    source_run_id: str,
    source_sequence: int,
) -> str:
    identity = [
        project,
        environment,
        provider,
        capability,
        operation,
        operation_id,
        source_run_id,
        str(source_sequence),
    ]
    return _sha256(_canonical_json(identity))


def evidence_payload_digest(event: EvidenceEvent) -> str:
    payload = event.model_dump(mode="json", exclude={"payload_digest"})
    return _sha256(_canonical_json(payload))


def create_evidence_event(
    *,
    operation_id: str,
    project: str,
    environment: str,
    provider: str,
    capability: str,
    operation: str,
    state: EvidenceState,
    source_run_id: str,
    source_sequence: int,
    occurred_at: datetime,
    recorded_at: datetime | None = None,
    artifact_references: tuple[ArtifactReference, ...] = (),
    metadata: dict[str, Any] | None = None,
) -> EvidenceEvent:
    recorded = recorded_at or occurred_at
    event_id = deterministic_event_id(
        project=project,
        environment=environment,
        provider=provider,
        capability=capability,
        operation=operation,
        operation_id=operation_id,
        source_run_id=source_run_id,
        source_sequence=source_sequence,
    )
    values = {
        "event_id": event_id,
        "operation_id": operation_id,
        "project": project,
        "environment": environment,
        "provider": provider,
        "capability": capability,
        "operation": operation,
        "state": state,
        "source_run_id": source_run_id,
        "source_sequence": source_sequence,
        "occurred_at": occurred_at,
        "recorded_at": recorded,
        "artifact_references": artifact_references,
        "metadata": metadata or {},
    }
    unchecked = EvidenceEvent.model_construct(payload_digest="sha256:" + "0" * 64, **values)
    values["payload_digest"] = evidence_payload_digest(unchecked)
    return EvidenceEvent.model_validate(values)
