# Reference architecture

## Purpose

This repository provides an Azure-first workflow template for repeatable machine-learning projects. It is not a churn application with generic utilities attached. The reusable platform is the primary product; churn is one executable reference scenario.

## R1 boundaries

The generated R1 project has four explicit responsibilities:

1. **Infrastructure** — Terraform provisions the project-owned Dev Azure ML boundary.
2. **ML lifecycle** — Azure ML jobs train, evaluate, conditionally register, and batch serve an explicit model version.
3. **Evidence** — append-only project-local events and receipts normalize lifecycle evidence.
4. **Delivery** — GitHub OIDC workflows plan/apply infrastructure and invoke lifecycle operations with pinned dependencies.

The manifest expresses product intent. A deterministic resolved plan applies platform defaults and provider capability rules before files are generated. No cloud provider SDK is required to resolve the plan.

Foundry, Search, Databricks, hybrid tools, online endpoints, monitoring, retraining, portfolio projection, and Bicep generation are excluded from R1: they remain roadmap/reference architecture. Existing assets for those areas are not evidence of R1 generated capability or R1 acceptance.

## Generic workflow

```text
manifest → validate → resolve → generate → Terraform plan/apply
→ train → evaluate → conditionally register → batch deploy/invoke → evidence
```

Scenario implementations provide the data, feature builder, task-specific trainer, evaluation configuration, and retrieval sources. `platform_core` owns contracts, lineage, gates, lifecycle state, response envelopes, and operational conventions.

## Environment isolation

One repository represents one product and may describe Dev/Test/Prod. Each environment has an independent resource group, state key, Azure ML workspace, storage boundary, and evidence container. R1 live acceptance covers Dev only.

## Provider and maturity contract

Providers advertise immutable capability descriptors. The default `stable_only` policy rejects preview and experimental capabilities unless explicitly permitted by both the manifest and CLI. Planned capabilities can never be generated.

## Lifecycle contract

Model versions are immutable. Evaluation produces a structured promotion decision; registration occurs only when it passes. Batch deployment requires an explicit version and never infers authority from `latest` or numeric ordering.

## Non-negotiable invariants

- No scenario data, model, customer, or endpoint names are hardcoded in `platform_core`.
- Every model version has immutable lineage metadata.
- A candidate with invalid data provenance cannot be promoted.
- `champion`, `challenger`, and `served` versions are reported independently.
- An explicit champion metric is supplied for comparison; registry ordering never determines authority.
- Generated deployment references an explicit immutable model version.
- Dev live deployment requires approval after local and static validation.

## Documentation changelog

| Version | Created | Modified | Who | Notes |
|---|---|---|---|---|
| 1.1.0 | 2026-08-07 | 2026-08-17 | Ray Swan / Claude | Merged in docs/template/architecture.md's unique content (purpose statement, generic workflow pipeline, non-negotiable invariants); that file is now a redirect stub. |
| 1.0.0-rc1 | 2026-08-07 | 2026-08-11 | Ray Swan / Codex | Narrowed the architecture to the R1 Terraform, Azure ML batch, evidence, and delivery responsibilities. |
| 0.2.0 | 2026-08-07 | 2026-08-07 | Ray Swan / Codex | Clarified reusable-template and scenario boundaries. |
| 0.1.0 | 2026-08-07 | 2026-08-07 | Ray Swan / Codex | Initial reference architecture. |
