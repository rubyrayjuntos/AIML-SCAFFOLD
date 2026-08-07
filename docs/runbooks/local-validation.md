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

Live deployment is a separate runbook and requires an approved Azure subscription, resource group, identities, private-network decision, Databricks workspace, and Foundry project.
