# Resource ownership model

| Resource area | Project template owns | Enterprise platform owns |
|---|---|---|
| Scenario tables and features | Yes | No |
| Model versions and aliases | Yes | No |
| Project serving endpoint | Yes | No |
| Project Container App | Yes | No |
| Project Key Vault secrets | Usually | Policy/guardrails |
| Unity Catalog metastore | No | Yes |
| Hub networking | No | Yes |
| Entra tenant and governance | No | Yes |
| GitHub OIDC application | Project integration | Enterprise governance |
| Central monitoring platform | Consumes | Yes |

The template must accept IDs for centrally owned resources and must not recreate or mutate those resources unexpectedly.

## Documentation changelog

| Version | Created | Modified | Who | Notes |
|---|---|---|---|---|
| 0.1.0 | 2026-08-07 | 2026-08-07 | Ray Swan / Codex | Initial shared-versus-project ownership model. |
