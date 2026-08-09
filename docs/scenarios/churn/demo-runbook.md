# Churn demo runbook

1. Show the scenario manifest and feature registry entry.
2. Show Bronze, Silver, and Gold tables in the environment catalog.
3. Show corpus row count, customer count, class balance, and data-quality gates.
4. Run training and inspect the MLflow lineage artifact.
5. Register a challenger and compare AUC/F1/accuracy with the champion.
6. Show the production approval boundary before alias movement.
7. Show the serving endpoint and independent model-version fields.
8. Open a customer drill-down using a real Telco customer ID.
9. Show the score, drivers, 30-day delta, evidence, and playbook action.
10. Invoke the Foundry grounded agent and inspect citations and response source.
11. Show CI/CD validation and deployment evidence.

## Verified dev evidence

The dev reference workflow was executed in the project Databricks workspace on 2026-08-07:

- Unity Catalog objects exist under `mlworkflow_dev`: Bronze source, Silver customers, Gold features and labels, and the `ops.feature_registry` table.
- The canonical 7,043-customer corpus passed ingestion, Silver, and Gold validation.
- Unity Catalog model `mlworkflow_dev.ml.churn_classifier` version `1` is `READY` with AUC `0.8377302436`, F1 `0.6158536585`, and accuracy `0.7317246274`.
- Explicit `challenger`, `champion`, and `served` aliases point to version `1`.
- Databricks Model Serving endpoint `churn-model-endpoint` is `READY` and serves version `1` at 100% traffic.
- The local API returned a live server-derived score for customer `7590-VHVEG` with feature version `churn.features.v1` and contract `churn_feature_contract_v1`.

Foundry remains contract-validated with the deterministic fallback; no live Foundry project or agent deployment was performed.

## Documentation changelog

| Version | Created | Modified | Who | Notes |
|---|---|---|---|---|
| 0.2.0 | 2026-08-07 | 2026-08-07 | Ray Swan / Codex | Recorded verified dev training, registration, serving, and API evidence; documented the Foundry limitation. |
| 0.1.0 | 2026-08-07 | 2026-08-07 | Ray Swan / Codex | Initial churn demo runbook. |
