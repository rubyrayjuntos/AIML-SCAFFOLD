# Resource ownership model

Three ownership categories, not two. R1 established the first two columns below. R3 (see `docs/decisions/0011-factory-reference-boundary.md`) adds the third: resources the factory itself procures and operates to prove a capability live, that are **not yet** expressed as a template module a generated project could provision for itself. A resource graduates out of "Factory owns" once its pattern is generalized into a template module — at that point a reference instance of it is simply "Project template owns: Yes," same as everything else below.

| Resource area | Project template owns | Enterprise platform owns | Factory owns (reference/proving-ground only) |
|---|---|---|---|
| Environment resource group | No | Provisioning and scoped grants | No |
| Terraform backend | No | State account, container, and access | No |
| Azure ML workspace | Yes, within assigned group | Policy/guardrails | No |
| Workspace system-assigned identity | Lifecycle tied to project workspace | Azure ML service creates its documented environment-scoped service role | No |
| Compute user-assigned identity | Yes, including storage data role | Policy/guardrails | No |
| Project storage and evidence container | Yes | Retention and classification policy | No |
| Model versions | Yes | No | No |
| Project batch endpoint | Yes | No | No |
| Project Key Vault | Yes | Policy/guardrails | No |
| OIDC federated credential | No | Provisioning and governance | No |
| Entra tenant and governance | No | Yes | No |
| Central portfolio evidence index | No in R1 | Deferred | No |

The manifest references centrally owned resources by immutable Azure resource ID. Generated Terraform operates only inside its assigned environment resource group. Existing Bicep must not target that group or co-manage any generated resource.

**No-accidental-inheritance invariant:** a generated project may inherit an architecture/configuration *contract* from a factory-owned resource, but never an undeclared *runtime dependency* on it. It must either provision its own equivalent resource, or explicitly declare consumption of a named, intentionally shared platform service. See ADR 0011 for the full rationale — this is the rule that would have prevented R3 Slice 1's cross-tenant Databricks dependency.

## R3 target-state inventory

Built 2026-08-17 for R3.1 (subscription consolidation + platform foundation — see project planning history). Declared-first, then live-verified against the primary subscription (`5b452321-32fd-4b1c-8bbf-6d69a5a587ad`, tenant `90a7175b-82cd-4815-9050-8cbae3a1d234`) via `az`/`gh`/`databricks` CLI on the date above. Scope is this repository (the factory floor) and the live estate it owns or should own on the primary subscription. `azure-mlops` is covered only in the historical appendix below, not as a parallel target architecture.

| Resource | Purpose | Factory-owned? | Generated-project-owned? | Shared-service candidate? | Terraform state owner | Identity | Migration action |
|---|---|---|---|---|---|---|---|
| `rg-azure-ai-ml-ops-dev` (resource group) | Churn reference app's environment boundary | Yes (reference instance) | No (structural pattern is project-template-owned; this instance is the reference) | No | `infra/` bootstrap state, container `azure-ai-ml-ops-r1` in shared backend | `gh-azure-ai-ml-ops-r1-dev-oidc` (scoped to generated repo `azure-aiml-ops`, verified live via `gh repo view` — correctly *not* scoped to the factory repo itself) | None — correctly governed already |
| `mlw-azure-ai-ml-ops-dev` (Azure ML workspace) + storage/KV/Log Analytics/App Insights/ACR/compute identity | Churn reference training/serving | Yes (reference instance) | No (project-template pattern) | No | Inferred to be the generated project template's own state (not this repo's `infra/` bootstrap state, which only creates the resource group + identity + role assignments) — **not directly confirmed**, see gaps below | Compute user-assigned identity `id-azure-ai-ml-ops-dev-compute` | None — resources themselves are R1/R2-proven and live-verified via `az resource list`; only the exact state-file location is unconfirmed |
| Terraform backend storage account `stazmlops0001devtf` / RG `rg-azmlops-0001dev-tf` | State storage for this repo's bootstrap Terraform | No — **shared** with the historical `azmlops` project (dedicated container `azure-ai-ml-ops-r1` within a shared account) | No | Yes, already de facto shared | N/A (this *is* the state backend) | N/A | Decide deliberately: keep sharing the account (document it as an intentional shared service) or split to a dedicated backend account for the factory. Not urgent, but currently implicit rather than declared |
| Azure Databricks workspace | Unity Catalog + Vector Search host for retrieval capability | Target: Yes (currently: **does not exist on this subscription**) | No | No | None yet | None yet | **R3.2**: provision via Terraform, `azure_foundation`-module pattern. Currently the live Databricks workspace is on a separate subscription/tenant (n2arts2000/Yahoo) — see historical appendix |
| Unity Catalog `mlworkflow_dev` (catalog/schemas/tables/model) | Churn feature/retrieval gold tables, registered model | Target: Yes (currently exists only on the Yahoo-tenant workspace) | No | No | N/A (Databricks-native, not Terraform-managed today) | Catalog owned by `n2arts2000@yahoo.com` on the old workspace | **R3.4**: recreate on the new Azure Databricks workspace; re-prove with the same evidence bar Slice 1 used |
| Vector Search endpoint `churn-retrieval-endpoint` + 3 indexes (`notes_vs`/`tickets_vs`/`playbooks_vs`) | Retrieval capability proven in Slice 1 | Target: Yes (currently exists only on the Yahoo-tenant workspace) | No | No | N/A (notebook-provisioned, not Terraform-managed) | Same as above | **R3.4**: recreate on the new workspace; acceptance criterion is identical retrieval evidence, entirely within the primary subscription |
| `Microsoft.CognitiveServices/accounts` `rswan-1970-resource` (kind `AIServices`) in `rg-RSwan-1970`, with `gpt-5` and `text-embedding-3-small` deployments | Foundry chat + embedding runtime | Yes — **adopted for R3.5** (live-verified 2026-08-17; pre-existing, not provisioned by this project) | No | Undecided — whether other future generated projects would consume this same reference deployment as a declared shared service, or each provision their own, is an R4+ question the no-accidental-inheritance invariant requires be answered explicitly rather than left implicit | None (not Terraform-managed today) | Whatever identity currently manages `rg-RSwan-1970` — not yet audited | **R3.2/R3.5**: import into Terraform state, wire `settings.foundry_endpoint`/`foundry_deployment` in `scenario.yaml`, confirm workload identity access (this is exactly what R3.3's identity gate exists to prove, not assume) |
| `settings.foundry_endpoint` / `settings.foundry_deployment` (config fields) | Application-level Foundry configuration | Yes | Contract yes, values no | No | N/A (application config, not infra) | N/A | Currently unset — no `foundry:` block in `scenario.yaml`. Populate once R3.5 lands |
| `foundry/tools/tools.contract.json`, `foundry/agents/*`, `foundry/evaluations/*` | Declared agent/tool/guardrail contract | Yes (contract-only, no live resource behind it yet) | Contract yes, once graduated to a template module | No | N/A | N/A | No infra action — tracked here so R4 doesn't start from a blank slate; contract already validated by `tests/contracts/test_foundry_contract.py` |
| `rg-azmlops-0001dev` / `rg-azmlops-0001prod` (Azure ML workspaces, endpoints, Cognitive Search, ACR, KV) | Historical `azmlops` accelerator's live footprint | No | No | No | Separate Terraform state, not this repo's | Separate Entra app `gh-azure-mlops-dev-oidc` | **Decision needed, not resolved in R3.1**: these are live and presumably billing, not merely historical code. Retire, or explicitly reclassify as an intentional legacy/comparison environment. See historical appendix |

**Explicit gaps left open by this inventory** (by design — R3.1 is research, not provisioning): the exact identity/RBAC currently governing `rg-RSwan-1970` has not been audited; whether the shared Terraform backend storage account should be split is undecided; the `azmlops` dev/prod retirement decision is deliberately deferred to a dedicated decision rather than bundled into this inventory; the exact Terraform state location for the generated Azure ML workspace/storage/KV/Log Analytics/App Insights/ACR resources is inferred from what `infra/`'s bootstrap module does *not* create, not confirmed via `terraform state list` against the actual state file.

### `azure-mlops` — historical appendix

Status: historical prior art, not a target architecture. Purpose: the original, pre-AIML-SCAFFOLD accelerator implementation (one of the "three repos" pattern this project moved away from — see ADR 0011). Its live Azure footprint (`rg-azmlops-0001dev`, `rg-azmlops-0001prod`, and their Terraform-state resource groups) is real and running in the same primary subscription, confirmed live 2026-08-17, but is not part of R3's consolidation target and no R3 decision should be designed around preserving compatibility with it. Retained here for provenance and for rescuing known-good implementation details only.

## Documentation changelog

| Version | Created | Modified | Who | Notes |
|---|---|---|---|---|
| 1.1.0 | 2026-08-17 | 2026-08-17 | Ray Swan / Claude | Added the "Factory owns" ownership category and the R3.1 target-state inventory (live-verified against the primary subscription), plus the `azure-mlops` historical appendix. |
| 1.0.0-rc2 | 2026-08-07 | 2026-08-12 | Ray Swan / Codex | Clarified project ownership of workspace and compute identities while retaining Azure ML ownership of its service-created role. |
| 1.0.0-rc1 | 2026-08-07 | 2026-08-11 | Ray Swan / Codex | Recorded R1 bootstrap, Terraform, Azure ML, identity, and evidence ownership. |
| 0.1.0 | 2026-08-07 | 2026-08-07 | Ray Swan / Codex | Initial shared-versus-project ownership model. |
