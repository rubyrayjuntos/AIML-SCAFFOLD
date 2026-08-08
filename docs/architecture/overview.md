# Reference architecture

## Boundaries

The template has four explicit planes:

1. **Data/ML plane** — Databricks, Unity Catalog, Delta tables, MLflow, and model serving.
2. **Application plane** — FastAPI and web UI in Azure Container Apps.
3. **Reasoning plane** — Azure AI Foundry grounded agent with approved application tools.
4. **Delivery/operations plane** — GitHub OIDC, Bicep, DABs, approvals, Application Insights, Log Analytics, and alerts.

The model-serving endpoint is the authority for inference. The API never loads a local model artifact or accepts a score from the browser.

Production deployments also create a user-assigned managed identity, RBAC-enabled Key Vault with soft-delete and purge protection, a private endpoint network, and private DNS for governed storage. Development may use public service endpoints only through the explicit `secureNetworkEnabled=false` profile.

## Environment isolation

Each environment receives an isolated resource group, catalog, storage boundary, and serving endpoint. Promotion moves code and model metadata through environments; it does not copy mutable tables or reuse a development model alias in production.

## Data contract

The churn source must contain exactly 7,043 distinct Telco customer IDs. Any disallowed synthetic rows, unexpected row count, missing identifier, schema mismatch, or invalid label domain fails the workflow before training.

## Lifecycle contract

Model versions are immutable. `@champion` and `@challenger` are aliases, not numeric defaults. Validation records the candidate lineage and comparison. Automated gates can reject candidates; production alias movement requires approval. Served version is tracked independently from champion version.

## Documentation changelog

| Version | Created | Modified | Who | Notes |
|---|---|---|---|---|
| 0.2.0 | 2026-08-07 | 2026-08-07 | Ray Swan / Codex | Clarified reusable-template and scenario boundaries. |
| 0.1.0 | 2026-08-07 | 2026-08-07 | Ray Swan / Codex | Initial reference architecture. |
