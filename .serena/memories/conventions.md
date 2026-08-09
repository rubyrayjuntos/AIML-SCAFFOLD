## Documentation

Every Markdown doc in this repo requires a "Documentation changelog" table at the end with columns: Version | Created | Modified | Who | Notes. Bump version and add a row on every substantive edit; do not silently edit without a changelog row.

## Platform vs scenario boundary (ADR 0002)

`src/platform_core` = domain-neutral contracts/orchestration only, no churn-specific assumptions. `src/scenarios/<name>` = scenario-specific data/features/models/playbooks/retrieval config. When adding scenario logic, prefer adapter code in the scenario dir over widening a platform_core contract; when changing platform_core, ask whether the change generalizes past churn before landing it.

## Security/identity defaults

Prefer managed identity, Entra OIDC, Key Vault references, least-privilege RBAC by default in any new Azure-touching code or IaC. Dev may disable private networking only via the explicit `secureNetworkEnabled=false` profile; prod requires private endpoints/DNS, RBAC-enabled Key Vault with soft-delete + purge protection, and a user-assigned managed identity.
