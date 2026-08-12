from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable

from platform_core.contracts.evidence import (
    TERMINAL_STATES,
    EvidenceEvent,
    OperationReceipt,
)

_ALLOWED_TRANSITIONS = {
    "started": {"running", "succeeded", "failed", "skipped"},
    "running": {"running", "succeeded", "failed", "skipped"},
}


def _error(code: str, event: EvidenceEvent, message: str) -> dict[str, str]:
    return {"code": code, "event_id": event.event_id, "message": message}


def _validate_timeline(events: list[EvidenceEvent]) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    first = events[0]
    if first.state.value != "started":
        errors.append(_error("MISSING_START_STATE", first, "operation does not begin with started"))
    context = (first.provider, first.capability, first.operation, first.source_run_id)
    seen_sequences: dict[int, EvidenceEvent] = {}
    terminal: EvidenceEvent | None = None
    previous: EvidenceEvent | None = None
    for event in events:
        if (event.provider, event.capability, event.operation, event.source_run_id) != context:
            errors.append(
                _error(
                    "CONTEXT_MISMATCH",
                    event,
                    "operation events do not share one source context",
                )
            )
        existing = seen_sequences.get(event.source_sequence)
        if existing and existing.payload_digest != event.payload_digest:
            errors.append(
                _error("SEQUENCE_REUSE", event, "source sequence is reused by different content")
            )
            if existing.event_id == event.event_id:
                errors.append(
                    _error(
                        "EVENT_ID_CONTENT_CONFLICT",
                        event,
                        "event identity is associated with different content",
                    )
                )
        seen_sequences[event.source_sequence] = event
        if terminal is not None and event.event_id != terminal.event_id:
            code = (
                "CONFLICTING_TERMINAL_STATE"
                if event.state in TERMINAL_STATES
                else "POST_TERMINAL_EVENT"
            )
            errors.append(_error(code, event, "event follows a terminal event"))
        if previous and terminal is None:
            allowed = _ALLOWED_TRANSITIONS.get(previous.state.value, set())
            if event.state.value not in allowed:
                errors.append(
                    _error(
                        "INVALID_STATE_TRANSITION",
                        event,
                        f"{event.state.value} does not follow {previous.state.value}",
                    )
                )
        if event.state in TERMINAL_STATES and terminal is None:
            terminal = event
        previous = event
    return errors


def project_operations(
    events: Iterable[EvidenceEvent],
    receipts: Iterable[OperationReceipt] = (),
) -> dict:
    unique_events: dict[tuple[str, str], EvidenceEvent] = {}
    conflicting_duplicates: list[EvidenceEvent] = []
    for event in events:
        key = (event.event_id, event.payload_digest)
        if key not in unique_events:
            if any(existing_id == event.event_id for existing_id, _ in unique_events):
                conflicting_duplicates.append(event)
            unique_events[key] = event
    ordered = sorted(
        unique_events.values(),
        key=lambda event: (
            event.project,
            event.environment,
            event.operation_id,
            event.source_sequence,
            event.occurred_at,
            event.event_id,
        ),
    )
    by_operation: dict[tuple[str, str, str], list[EvidenceEvent]] = defaultdict(list)
    for event in ordered:
        by_operation[(event.project, event.environment, event.operation_id)].append(event)
    receipts_by_operation: dict[tuple[str, str, str], list[OperationReceipt]] = defaultdict(list)
    for receipt in receipts:
        receipts_by_operation[receipt.operation_key].append(receipt)
    operations = []
    for operation_key, operation_events in sorted(by_operation.items()):
        project, environment, operation_id = operation_key
        latest = operation_events[-1]
        errors = _validate_timeline(operation_events)
        for duplicate in conflicting_duplicates:
            if (
                duplicate.project,
                duplicate.environment,
                duplicate.operation_id,
            ) == operation_key and not any(
                error["event_id"] == duplicate.event_id
                and error["code"] == "EVENT_ID_CONTENT_CONFLICT"
                for error in errors
            ):
                errors.append(
                    _error(
                        "EVENT_ID_CONTENT_CONFLICT",
                        duplicate,
                        "event identity is associated with different content",
                    )
                )
        operation_receipts = receipts_by_operation.get(operation_key, [])
        receipt = operation_receipts[0] if len(operation_receipts) == 1 else None
        if len(operation_receipts) > 1:
            serialized = {
                item.model_dump_json() for item in operation_receipts
            }
            code = "DUPLICATE_RECEIPT" if len(serialized) == 1 else "CONFLICTING_RECEIPT"
            errors.append(
                _error(
                    code,
                    latest,
                    "operation has more than one receipt",
                )
            )
        terminal = latest.state in TERMINAL_STATES
        receipt_matches = bool(
            terminal
            and receipt
            and receipt.terminal_event_id == latest.event_id
            and receipt.state == latest.state
            and receipt.artifact_references == latest.artifact_references
        )
        if receipt and not receipt_matches:
            errors.append(
                _error("RECEIPT_MISMATCH", latest, "receipt does not match the terminal event")
            )
        integrity = "invalid" if errors else "valid"
        complete = bool(not errors and receipt_matches)
        projection_status = "invalid" if errors else ("complete" if complete else "incomplete")
        operations.append(
            {
                "operation_id": operation_id,
                "project": project,
                "environment": environment,
                "operation": latest.operation,
                "provider": latest.provider,
                "capability": latest.capability,
                "state": "invalid" if errors else latest.state.value,
                "observed_state": latest.state.value,
                "integrity": integrity,
                "projection_status": projection_status,
                "complete": complete,
                "errors": errors,
                "event_count": len(operation_events),
                "started_at": operation_events[0].occurred_at.isoformat(),
                "updated_at": latest.occurred_at.isoformat(),
                "source_run_id": latest.source_run_id,
                "artifact_references": [
                    artifact.model_dump(mode="json")
                    for artifact in latest.artifact_references
                ],
            }
        )
    return {"operations": operations, "operation_count": len(operations)}
