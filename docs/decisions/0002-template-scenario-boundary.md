# ADR 0002: Separate reusable template from reference scenarios

## Decision

The repository treats reusable platform contracts and orchestration as the primary product. Churn-specific data, features, models, playbooks, retrieval indexes, and demo behavior live under a scenario boundary.

## Rationale

This prevents a toy or domain-specific assumption from becoming a platform invariant. It also makes adding fraud, forecasting, recommendation, or document-routing scenarios possible without copying or modifying `platform_core`.

## Consequences

- Scenario manifests become required configuration.
- Platform contracts must remain domain-neutral.
- The churn demo carries more adapter code, but that code is explicit and reusable.
- Template changes and scenario changes can be versioned and reviewed independently.

## Documentation changelog

| Version | Created | Modified | Who | Notes |
|---|---|---|---|---|
| 0.1.0 | 2026-08-07 | 2026-08-07 | Ray Swan / Codex | Initial template/scenario boundary decision. |
