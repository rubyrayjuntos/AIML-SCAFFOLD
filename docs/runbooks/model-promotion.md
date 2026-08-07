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

Model versions are never silently renumbered or overwritten. Retention/deletion is a separate reviewed operation.
