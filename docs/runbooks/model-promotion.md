# Model promotion runbook

1. Run the DAB training job in the target non-production catalog.
2. Verify source count, source identifier, schema version, label domain, and disallowed-row count.
3. Inspect the MLflow run and lineage artifact.
4. Compare the candidate with the current champion using the configured primary metric and improvement gate.
5. Require production approval in the GitHub Environment.
6. Move the Unity Catalog `champion` alias.
7. Update the serving endpoint to the exact approved model version.
8. Verify that `served_version`, `champion_version`, and candidate state are independently reported.
9. Run score, API, and Foundry smoke tests.

For the dev reference path, use `scripts/promote_dev_model.py` with the exact registered version and observed candidate AUC. The script requires `--approve`, sets `challenger`, `champion`, and `served` explicitly, and creates or updates only `churn-model-endpoint`.

Model versions are never silently renumbered or overwritten. Retention/deletion is a separate reviewed operation.

## Documentation changelog

| Version | Created | Modified | Who | Notes |
|---|---|---|---|---|
| 0.2.0 | 2026-08-07 | 2026-08-07 | Ray Swan / Codex | Added explicit dev promotion and serving endpoint procedure. |
| 0.1.0 | 2026-08-07 | 2026-08-07 | Ray Swan / Codex | Initial model promotion runbook. |
