# Agent instructions

## Project purpose

This repository is an Azure-first, reusable enterprise ML workflow template. The churn implementation is a reference scenario, not the platform definition.

## Scope boundaries

- Keep reusable contracts and orchestration domain-neutral under `src/platform_core`.
- Keep Telco/churn data, features, models, playbooks, and retrieval configuration under the churn scenario boundary.
- Do not copy code, data, schemas, model versions, or deployment state from the legacy `cust-churn` project.
- Do not deploy into legacy Azure resources unless the user explicitly requests a migration or comparison.

## Implementation rules

- Prefer managed identity, Entra OIDC, Key Vault references, and least-privilege RBAC.
- Bicep is the authoritative Azure IaC path; Terraform is portability-only and must not manage the same resources.
- Databricks code is deployed with Asset Bundles.
- Model versions are immutable; aliases identify lifecycle roles.
- Never use numeric model-version defaults as lifecycle state.
- Never allow client-provided scores, drivers, or deltas to override server-derived context.
- Foundry tools must be allowlisted, read-only application functions unless a future ADR explicitly changes that policy.
- Add or update tests with behavior changes.
- Every Markdown document requires a versioned changelog containing version, created date, modified date, who, and notes.

## Validation

Run before handoff:

```bash
pytest
ruff check .
az bicep build --file infra/bicep/main.bicep
terraform -chdir=infra/terraform validate
DATABRICKS_BUNDLE_ROOT=databricks databricks bundle validate -t dev
```

## Tool preference

When available, use Azure MCP for Azure resource/IaC context, Foundry MCP for Foundry projects/models/agents, Azure DevOps MCP for Azure DevOps artifacts, and Serena or an equivalent semantic project-context server for repository navigation. Use local CLI tools as the fallback and record any unavailable server capability in the handoff.

## Documentation changelog

| Version | Created | Modified | Who | Notes |
|---|---|---|---|---|
| 0.1.0 | 2026-08-07 | 2026-08-07 | Ray Swan / Codex | Initial repository-specific agent instructions. |
