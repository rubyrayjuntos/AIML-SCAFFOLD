# Template lifecycle and versioning

## Template versions

The template is versioned independently from scenarios. A scenario declares the compatible template version in its manifest.

Changes that alter contracts, deployment interfaces, lineage requirements, or promotion semantics require a major or minor template version according to semantic-versioning policy.

## Model lifecycle

Model versions are immutable records. Aliases identify roles:

- `challenger`: candidate under validation;
- `champion`: approved registry version;
- `served`: version receiving endpoint traffic.

Numeric version order is never used as a proxy for promotion state.

## Retention

Model deletion is a separate reviewed operation. Promotion never deletes historical versions automatically because rollback and auditability are required enterprise capabilities.

## Documentation changelog

| Version | Created | Modified | Who | Notes |
|---|---|---|---|---|
| 0.1.0 | 2026-08-07 | 2026-08-07 | Ray Swan / Codex | Initial lifecycle and versioning policy. |
