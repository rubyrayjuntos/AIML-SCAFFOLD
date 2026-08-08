# Template configuration

## Configuration boundary

Environment configuration selects Azure resources and deployment targets. Scenario manifests select data and ML behavior. Neither may contain credentials.

## Environment configuration

Each environment supplies:

- subscription and resource group;
- region and network profile;
- catalog name;
- Databricks workspace and serving endpoint;
- Foundry project/deployment references;
- Key Vault and monitoring references;
- deployment identity and approval policy.

Recommended names follow `organization-project-environment`, for example `acme-churn-dev`. Production configuration must not inherit development resource identifiers.

## Scenario configuration

Each scenario supplies:

- source datasets and expected data contract;
- feature builder and feature registry entry;
- task type and candidate models;
- evaluation metrics and thresholds;
- model name and serving endpoint;
- retrieval indexes and playbook sources.

The canonical example is [the churn scenario manifest](../scenarios/churn/scenario.yaml).

## Secret handling

Configuration may reference secrets by Key Vault name or secret reference, but must never contain secret values, tokens, connection strings, or personal access credentials.

## Documentation changelog

| Version | Created | Modified | Who | Notes |
|---|---|---|---|---|
| 0.1.0 | 2026-08-07 | 2026-08-07 | Ray Swan / Codex | Initial configuration contract. |
