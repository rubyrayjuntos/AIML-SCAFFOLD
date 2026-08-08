# Enterprise ML Workflow

Azure-first, config-driven machine-learning workflow template with a clean Telco churn reference scenario.

This repository is intentionally independent of the previous churn prototype. It does not import its code, data, schemas, model registry, or deployment state.

## Architecture

The supported path is:

`ingest → validate → bronze → silver → gold/features → train → evaluate → register → approve → promote → serve → monitor`

Azure resources are authored in Bicep. Terraform is a separate portability implementation and must not manage the same resource group. Databricks code is delivered with Asset Bundles. Foundry is used for grounded, structured explanations over application-approved tools.

## Documentation map

- [Template architecture](docs/template/architecture.md)
- [Template configuration](docs/template/configuration.md)
- [Extension guide](docs/template/extension-guide.md)
- [Deployment guide](docs/template/deployment.md)
- [Template lifecycle](docs/template/lifecycle.md)
- [Resource ownership](docs/architecture/resource-ownership.md)
- [Environment strategy](docs/architecture/environment-strategy.md)
- [Churn scenario](docs/scenarios/churn/README.md)
- [Churn data contract](docs/scenarios/churn/data-contract.md)
- [Churn feature catalog](docs/scenarios/churn/feature-catalog.md)
- [Churn evaluation](docs/scenarios/churn/evaluation.md)
- [Churn demo runbook](docs/scenarios/churn/demo-runbook.md)
- [Development tooling and context servers](docs/template/tooling.md)

The repository is a reusable template first. Churn is a reference scenario built on top of the template; scenario-specific assumptions must not leak into `platform_core`.

## Local validation

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
ruff check .
pytest
```

## Deployment profiles

`dev` is a lower-cost profile with explicitly documented network tradeoffs. `test` and `prod` are isolated catalogs/environments. Production requires private connectivity, managed identity, Key Vault, RBAC, diagnostics, and an approval gate before model cutover.

## Churn scenario

The scenario uses the canonical 7,043-record Telco Customer Churn corpus. The source is downloaded by the Databricks ingestion task and validated before any downstream table or model is produced. No synthetic customers are part of the scenario.

## Status

This initial scaffold establishes the contracts and deployment boundaries. Azure resource deployment, Databricks workspace configuration, Foundry resource binding, and live model registration are explicit environment steps and are not performed by local tests.

## Documentation changelog

| Version | Created | Modified | Who | Notes |
|---|---|---|---|---|
| 0.2.0 | 2026-08-07 | 2026-08-07 | Ray Swan / Codex | Added template/scenario documentation boundary and documentation map. |
| 0.1.0 | 2026-08-07 | 2026-08-07 | Ray Swan / Codex | Initial repository orientation. |
