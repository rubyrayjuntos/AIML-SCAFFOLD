# Environment strategy

## Isolation

Development, test, and production use separate resource groups and catalogs. Recommended catalogs are `mlworkflow_dev`, `mlworkflow_test`, and `mlworkflow_prod`, unless enterprise governance supplies a different naming convention.

Each environment has independent:

- data write boundaries;
- model registry namespace;
- serving endpoint;
- secrets and managed identity;
- deployment approval policy.

## Promotion

Code and configuration move through CI/CD. Production data, model aliases, and serving traffic are not mutated by development workflows.

## Profiles

- `dev`: lower-cost, explicit public-network tradeoffs where necessary;
- `test`: production-shaped validation and integration environment;
- `prod`: private networking, managed identity, Key Vault, diagnostics, approval, and retention controls.

## Documentation changelog

| Version | Created | Modified | Who | Notes |
|---|---|---|---|---|
| 0.1.0 | 2026-08-07 | 2026-08-07 | Ray Swan / Codex | Initial environment isolation strategy. |
