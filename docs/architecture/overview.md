# Reference architecture

## R1 boundaries

The generated R1 project has four explicit responsibilities:

1. **Infrastructure** — Terraform provisions the project-owned Dev Azure ML boundary.
2. **ML lifecycle** — Azure ML jobs train, evaluate, conditionally register, and batch serve an explicit model version.
3. **Evidence** — append-only project-local events and receipts normalize lifecycle evidence.
4. **Delivery** — GitHub OIDC workflows plan/apply infrastructure and invoke lifecycle operations with pinned dependencies.

The manifest expresses product intent. A deterministic resolved plan applies platform defaults and provider capability rules before files are generated. No cloud provider SDK is required to resolve the plan.

Foundry, Search, Databricks, hybrid tools, online endpoints, monitoring, retraining, portfolio projection, and Bicep generation are excluded from R1. Existing assets for those areas are not evidence of R1 generated capability.

## Environment isolation

One repository represents one product and may describe Dev/Test/Prod. Each environment has an independent resource group, state key, Azure ML workspace, storage boundary, and evidence container. R1 live acceptance covers Dev only.

## Provider and maturity contract

Providers advertise immutable capability descriptors. The default `stable_only` policy rejects preview and experimental capabilities unless explicitly permitted by both the manifest and CLI. Planned capabilities can never be generated.

## Lifecycle contract

Model versions are immutable. Evaluation produces a structured promotion decision; registration occurs only when it passes. Batch deployment requires an explicit version and never infers authority from `latest` or numeric ordering.

## Documentation changelog

| Version | Created | Modified | Who | Notes |
|---|---|---|---|---|
| 1.0.0-rc1 | 2026-08-07 | 2026-08-11 | Ray Swan / Codex | Narrowed the architecture to the R1 Terraform, Azure ML batch, evidence, and delivery responsibilities. |
| 0.2.0 | 2026-08-07 | 2026-08-07 | Ray Swan / Codex | Clarified reusable-template and scenario boundaries. |
| 0.1.0 | 2026-08-07 | 2026-08-07 | Ray Swan / Codex | Initial reference architecture. |
