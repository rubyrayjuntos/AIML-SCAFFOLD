# ADR 0004: R1 evidence is project-local and append-only

## Decision

Each generated environment owns a private `platform-evidence` container in its Azure ML storage account. Evidence events use deterministic identifiers and create-only writes beneath immutable run-specific paths. A duplicate identifier with the same digest is idempotent; different content is rejected.

Event identity algorithm `1.0` hashes a canonical JSON array containing these ordered inputs: project, environment, provider, capability, operation, operation ID, source run ID, and source sequence. The `event_identity_version` field is required so a future algorithm change cannot silently reinterpret stored evidence.

The event payload contains operational metadata, hashes, provider identifiers, metrics, and immutable artifact references. Artifact references use approved, unsigned URI schemes and reject user information, query strings, fragments, connection strings, and control characters. Validation errors never echo a rejected URI. Evidence must not contain credentials, tokens, raw training data, prompts, or sensitive inference payloads.

R1 provides a local read-only projector. Events and receipts are correlated by the composite identity `(project, environment, operation_id)`; operation IDs are not assumed globally unique. `OperationReceipt` therefore requires project and environment. A valid non-terminal timeline is `incomplete`; one valid terminal event with exactly one matching receipt is `complete`; transition, sequence, context, identity, terminal, duplicate-receipt, conflicting-receipt, or receipt-content conflicts are `invalid`. Invalid events remain visible with stable error codes, and the projector never chooses between conflicting terminal outcomes or receipts. Projection is deterministic regardless of iterable order. Central portfolio ingestion and a managed query index are deferred.

## Retention and rollback

The manifest supplies evidence retention, with 90 days as the R1 default. Blob versioning is enabled. Evidence is never deleted as an application rollback action.

## Documentation changelog

| Version | Created | Modified | Who | Notes |
|---|---|---|---|---|
| 0.3.0 | 2026-08-11 | 2026-08-11 | Ray Swan / Codex | Added composite project/environment/operation receipt identity and deterministic duplicate/conflict rejection. |
| 0.2.0 | 2026-08-11 | 2026-08-11 | Ray Swan / Codex | Versioned event identity, canonicalized artifact URIs, and defined visible timeline integrity outcomes. |
| 0.1.0 | 2026-08-11 | 2026-08-11 | Ray Swan / Codex | Selected project-local Blob evidence, deterministic idempotency, and read-only projection for R1. |
