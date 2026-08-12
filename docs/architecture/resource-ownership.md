# Resource ownership model

| Resource area | Project template owns | Enterprise platform owns |
|---|---|---|
| Environment resource group | No | Provisioning and scoped grants |
| Terraform backend | No | State account, container, and access |
| Azure ML workspace | Yes, within assigned group | Policy/guardrails |
| Project storage and evidence container | Yes | Retention and classification policy |
| Model versions | Yes | No |
| Project batch endpoint | Yes | No |
| Project Key Vault | Yes | Policy/guardrails |
| OIDC federated credential | No | Provisioning and governance |
| Entra tenant and governance | No | Yes |
| Central portfolio evidence index | No in R1 | Deferred |

The manifest references centrally owned resources by immutable Azure resource ID. Generated Terraform operates only inside its assigned environment resource group. Existing Bicep must not target that group or co-manage any generated resource.

## Documentation changelog

| Version | Created | Modified | Who | Notes |
|---|---|---|---|---|
| 1.0.0-rc1 | 2026-08-07 | 2026-08-11 | Ray Swan / Codex | Recorded R1 bootstrap, Terraform, Azure ML, identity, and evidence ownership. |
| 0.1.0 | 2026-08-07 | 2026-08-07 | Ray Swan / Codex | Initial shared-versus-project ownership model. |
