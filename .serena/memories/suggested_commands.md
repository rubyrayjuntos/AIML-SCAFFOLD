## Setup + local validation (from repo root)

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

Live deployment (Azure subscription/resource group/identities/network/Databricks workspace/Foundry project) is a separate runbook, not part of local validation — see `docs/template/deployment.md`.

## MCP/tool preference (from AGENTS.md)

Prefer Azure MCP (resources/IaC), Foundry MCP (Foundry projects/models/agents), Azure DevOps MCP (work items/pipelines), Serena (repo semantic navigation) over raw CLI when available. If an expected MCP server is unavailable, state the limitation explicitly rather than silently falling back to CLI without saying so.
