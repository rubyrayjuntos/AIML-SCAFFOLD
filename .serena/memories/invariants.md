## Pipeline (canonical, do not shortcut)

`ingest → validate → bronze → silver → gold/features → train → evaluate → register → validate challenger → approve → promote → serve → monitor`

## Four platform planes

1. Data/ML — Databricks, Unity Catalog, Delta, MLflow, model serving (authority for inference; API never loads a local model artifact or accepts a client-provided score).
2. Application — FastAPI + web UI on Azure Container Apps.
3. Reasoning — Azure AI Foundry grounded agent, approved read-only application tools only (allowlisted; changing to non-read-only requires a future ADR).
4. Delivery/ops — GitHub OIDC, Bicep, Databricks Asset Bundles, Terraform (portability only), Application Insights, Log Analytics, alerts.

## Non-negotiables

- No scenario (churn) data/model/customer/endpoint names hardcoded in `platform_core`.
- Every model version has immutable lineage metadata; `champion`/`challenger`/`served` are aliases tracked independently — never use a numeric model version as lifecycle state.
- A candidate with invalid data provenance cannot be promoted.
- Client-provided scores/drivers/deltas must never override server-derived context.
- Production promotion requires an approval gate after automated validation.
- Bicep is authoritative IaC (ADR 0001); Terraform targets a separate resource group/state and must never manage the same resources.
- Each environment (dev/test/prod) is fully isolated: separate resource group, catalog, storage boundary, serving endpoint. Promotion moves code/model metadata, never copies mutable tables or reuses a dev model alias in prod.
- Churn data contract: exactly 7,043 distinct Telco customer IDs, no synthetic rows; any row-count/schema/label mismatch fails the workflow before training.
- Resource ownership split: project template owns scenario tables/features/model versions/serving endpoint/Container App; enterprise platform owns Unity Catalog metastore, hub networking, Entra tenant/governance (see `docs/architecture/resource-ownership.md` for the full table).
