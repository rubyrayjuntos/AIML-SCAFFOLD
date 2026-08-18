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

### Retrieval evidence (R3 Slice 1, 2026-08-17)

The `seed_retrieval_gold` and `build_vector_indexes` tasks were run against `mlworkflow_dev` (job `938590502561545`, run `149113176952028`):

- `gold.customer_notes` (2 rows), `gold.support_tickets` (1 row), and `gold.recommended_actions` (3 rows) were seeded with authored content keyed to real customer IDs, per `docs/decisions` sourcing discipline.
- Vector Search endpoint `churn-retrieval-endpoint` (`STANDARD`) is online with three Delta Sync indexes, all `ready: true`: `notes_vs` (2 rows), `tickets_vs` (1 row), `playbooks_vs` (3 rows).
- A live `query_index` against `notes_vs`, filtered to `customer_id = "7590-VHVEG"` with query text `"usage dropped significantly, considering cheaper plan"`, returned exactly the seeded usage-drop note (score `0.734`):
  > "Customer reported a significant drop in monthly usage over the last billing cycle and asked about switching to a lower-cost plan. Flagged as a usage-drop risk signal for the retention team."
- A live `query_index` against `playbooks_vs` (no filter) for `"customer usage dropped, considering a cheaper plan, month-to-month contract"` ranked `action-usage-drop-outreach` first (score `0.756`), ahead of the stable-check-in and support-escalation playbooks — a content match, not just presence.
- Retrieval is proven at the adapter/data layer only in this slice: `src/scenarios/churn/retrieval.py` is unused by any HTTP route, and the Foundry/LLM call site is still the deterministic fallback described above.

Two genuine defects were found and fixed live during this run, both now committed: a PySpark column-resolution bug in `03a_seed_retrieval_gold.py` (referencing columns from separately-instantiated `spark.table(...)` calls), and a `databricks-sdk` version mismatch in the `churn_runtime` job environment (`EmbeddingSourceColumn` lacked `embedding_model_endpoint_name`, and `VectorIndexStatus` on the ambient SDK has no `detailed_state` field, only `ready` — the index-readiness polling in `03b_build_vector_indexes.py` was rewritten around `status.ready`).

## Documentation changelog

| Version | Created | Modified | Who | Notes |
|---|---|---|---|---|
| 0.3.0 | 2026-08-17 | 2026-08-17 | Ray Swan / Claude | Recorded live retrieval proof (gold tables, vector indexes, query results) for R3 Slice 1. |
| 0.2.0 | 2026-08-07 | 2026-08-07 | Ray Swan / Codex | Recorded verified dev training, registration, serving, and API evidence; documented the Foundry limitation. |
| 0.1.0 | 2026-08-07 | 2026-08-07 | Ray Swan / Codex | Initial churn demo runbook. |
