# Template operations

## Required operational signals

- workflow success/failure;
- data-quality gate results;
- model lineage and evaluation metrics;
- champion, challenger, and served versions;
- serving latency and errors;
- feature drift and prediction distribution;
- Foundry latency, failures, grounding, and citation compliance;
- deployment and approval audit trail.

R1 normalizes generated lifecycle signals as `EvidenceEvent` records in the environment-owned `platform-evidence` container. Event identity algorithm `1.0` includes project, environment, provider, capability, operation, operation ID, source run ID, and sequence. The local projector applies source sequence rather than arrival order, keeps invalid timelines visible, and marks an operation complete only when exactly one valid terminal outcome and matching receipt exist.

Evidence may include hashes, metrics, identifiers, and immutable artifact references. It must not include credentials, tokens, raw training data, prompts, or sensitive inference payloads. Evidence is retained during rollback.

## Incident response

Operators must be able to identify the exact served model version, revert the serving endpoint to the previous approved version, and distinguish a model failure from a data, endpoint, or Foundry failure.

## Documentation changelog

| Version | Created | Modified | Who | Notes |
|---|---|---|---|---|
| 1.0.0-rc2 | 2026-08-07 | 2026-08-11 | Ray Swan / Codex | Added versioned evidence identity and explicit incomplete, invalid, and complete projection semantics. |
| 1.0.0-rc1 | 2026-08-07 | 2026-08-11 | Ray Swan / Codex | Added the R1 project-local evidence and completion semantics. |
| 0.1.0 | 2026-08-07 | 2026-08-07 | Ray Swan / Codex | Initial template operations policy. |
