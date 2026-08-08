# Enterprise ML workflow template architecture

## Purpose

This repository provides an Azure-first workflow template for repeatable machine-learning projects. It is not a churn application with generic utilities attached. The reusable platform is the primary product; churn is one executable reference scenario.

## Platform planes

1. **Data and ML plane** — Azure Databricks, Unity Catalog, Delta tables, feature contracts, MLflow, and model serving.
2. **Application plane** — versioned API and web application hosted on Azure Container Apps.
3. **Reasoning plane** — Azure AI Foundry grounded agent using approved, read-only application tools.
4. **Delivery and operations plane** — GitHub OIDC, Bicep, Databricks Asset Bundles, Terraform portability, monitoring, and approval gates.

## Generic workflow

```text
ingest → validate → bronze → silver → gold/features → train → evaluate
→ register → validate challenger → approve → promote → serve → monitor
```

Scenario implementations provide the data, feature builder, task-specific trainer, evaluation configuration, and retrieval sources. `platform_core` owns contracts, lineage, gates, lifecycle state, response envelopes, and operational conventions.

## Non-negotiable invariants

- No scenario data, model, customer, or endpoint names are hardcoded in `platform_core`.
- Every model version has immutable lineage metadata.
- A candidate with invalid data provenance cannot be promoted.
- `champion`, `challenger`, and `served` versions are reported independently.
- Foundry tools are explicitly authorized and read-only by default.
- Production deployment requires approval after automated validation.

## Documentation changelog

| Version | Created | Modified | Who | Notes |
|---|---|---|---|---|
| 0.1.0 | 2026-08-07 | 2026-08-07 | Ray Swan / Codex | Initial template architecture definition. |
