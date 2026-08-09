Run before considering any task/handoff done (from `AGENTS.md`):

```bash
pytest
ruff check .
az bicep build --file infra/bicep/main.bicep
terraform -chdir=infra/terraform validate
DATABRICKS_BUNDLE_ROOT=databricks databricks bundle validate -t dev
```

Also required:
- Add or update tests with any behavior change.
- If a Markdown doc was added/edited, it must carry/update a versioned changelog table (version, created date, modified date, who, notes) — see `mem:conventions`.
- Verify no scenario-specific (churn) names/data leaked into `platform_core`, and no legacy `cust-churn` code/data/secrets were copied in.
