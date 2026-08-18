# ADR 0006: R1 provenance and provider extensions are deterministic contracts

## Decision

Every generated R1 repository contains three distinct provenance artifacts:

- `platform/source-manifest.yaml` is normalized user-supplied intent and excludes unresolved defaults.
- `platform/resolved-plan.json` contains selected providers, normalized Azure ML extensions, applied defaults, topology, resources, warnings, preconditions, maturity authorization, and approval policy.
- `generation-receipt.json` attests to the source manifest, resolved plan, template set, dependency constraints, generated tree, and platform release.

The source manifest and resolved plan are tracked generated files and therefore participate in the generated-tree digest. The receipt is excluded from that tree digest and recomputes every constituent digest during verification.

Azure ML provider extensions use a provider-specific model with unknown fields forbidden. Location and compute values are normalized before plan resolution. A normalized extension change alters the resolved-plan, generated-tree, and generation digests.

## Dependency updates

Generated CI and local instructions install through `constraints.txt`. The Azure ML training environment remains exactly pinned. Dependency changes occur in the platform template, require regeneration and conformance, and produce a new template and generated-tree identity.

## Documentation changelog

| Version | Created | Modified | Who | Notes |
|---|---|---|---|---|
| 0.1.0 | 2026-08-11 | 2026-08-11 | Ray Swan / Codex | Defined R1 provenance, provider-extension normalization, and constrained dependency updates. |
