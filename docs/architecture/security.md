# Security baseline

- GitHub Actions authenticates to Azure with Entra federated credentials and short-lived OIDC tokens.
- Workloads use managed identities; secrets are stored in RBAC-enabled Key Vault.
- Production storage and Key Vault disable public network access and use private endpoints/private DNS.
- CI identities and runtime identities are separate and receive least-privilege roles.
- Foundry tools are read-only application functions; arbitrary SQL and mutation are prohibited.
- Logs and traces include correlation IDs but never customer secrets or access tokens.
- Development exceptions are explicit in the deployment profile and cannot silently apply to production.
