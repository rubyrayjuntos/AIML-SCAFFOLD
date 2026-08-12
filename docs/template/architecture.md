# Enterprise ML workflow template architecture

## Purpose

This repository provides an Azure-first workflow template for repeatable machine-learning projects. It is not a churn application with generic utilities attached. The reusable platform is the primary product; churn is one executable reference scenario.

## R1 platform kernel

1. **Intent and policy** — manifest validation, maturity policy, provider discovery, and deterministic plan resolution.
2. **Generated infrastructure** — Terraform for the isolated Azure ML project environment.
3. **Generated ML lifecycle** — Azure ML training, evaluation, conditional registration, and batch serving.
4. **Evidence and delivery** — project-local evidence, GitHub OIDC, pinned workflows, and approval gates.

The earlier Databricks, application, and Foundry planes remain roadmap/reference architecture. They are not R1 generated capabilities or R1 acceptance evidence.

## Generic workflow

```text
manifest → validate → resolve → generate → Terraform plan/apply
→ train → evaluate → conditionally register → batch deploy/invoke → evidence
```

Scenario implementations provide the data, feature builder, task-specific trainer, evaluation configuration, and retrieval sources. `platform_core` owns contracts, lineage, gates, lifecycle state, response envelopes, and operational conventions.

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
| 1.0.0-rc1 | 2026-08-07 | 2026-08-11 | Ray Swan / Codex | Defined the R1 contract, Terraform, Azure ML batch, evidence, and delivery kernel. |
| 0.1.0 | 2026-08-07 | 2026-08-07 | Ray Swan / Codex | Initial template architecture definition. |
