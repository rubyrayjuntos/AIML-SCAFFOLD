# Local validation

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
ruff check .
pytest
az bicep build --file infra/bicep/main.bicep
terraform -chdir=infra/terraform init -backend=false
terraform -chdir=infra/terraform validate
DATABRICKS_BUNDLE_ROOT=databricks databricks bundle validate -t dev
```

The Bicep and Databricks commands validate deferred reference assets; they are not R1 generated-capability evidence. Follow the R1 local generation runbook for factory conformance.

Live deployment is a separate, approval-gated runbook and requires approved Azure bootstrap resources and identities. Databricks and Foundry are not R1 prerequisites.

## Documentation changelog

| Version | Created | Modified | Who | Notes |
|---|---|---|---|---|
| 1.0.0-rc1 | 2026-08-07 | 2026-08-11 | Ray Swan / Codex | Distinguished R1 conformance from deferred Bicep and Databricks reference validation. |
| 0.1.0 | 2026-08-07 | 2026-08-07 | Ray Swan / Codex | Initial local validation runbook. |
