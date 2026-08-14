# R1 Azure ML Dev infrastructure deployment plan

> **Status:** R1 Dev infrastructure apply complete (8 resources); Azure ML workload lifecycle remains unexercised

Generated: 2026-08-12

## 1. Project overview

**Goal:** Make local execution the default Dev lifecycle, make Azure training and batch compute independently configurable and explicitly authorized, regenerate a non-taxi Dev candidate, produce and review a replacement saved Terraform plan, and stop before apply or any charged Azure ML workload.

**Path:** Modify the existing Azure-first AIML-SCAFFOLD factory and regenerate the product repository. Do not edit generated lifecycle source manually.

## 2. Requirements

| Attribute | Value |
|---|---|
| Classification | Development; R1 preview |
| Scale | Small; one product and one Dev environment |
| Budget | Local-first; optional Dev cloud compute is serverless or scale-to-zero and limited to one node |
| Subscription | Azure subscription 1 (`5b452321-32fd-4b1c-8bbf-6d69a5a587ad`) |
| Tenant | `90a7175b-82cd-4815-9050-8cbae3a1d234` |
| Location | East US (`eastus`) |
| Data classification | Internal |
| Deployment approval | Deliberate, digest-bound owner authorization; not independent approval |

The manifest is authoritative for subscription, tenant, location, environment, ownership, and policy. The subscription has one enforced Azure Security Center default policy assignment; no discovered assignment changes the reviewed R1 Dev resource contract.

## 3. Components detected

| Component | Type | Technology | Path |
|---|---|---|---|
| Factory CLI and contracts | Python package | Python 3.11/3.12, Pydantic, Jinja | `src/aiml_scaffold/`, `src/platform_core/` |
| Generated infrastructure | Infrastructure as code | Terraform 1.10.0, AzureRM 4.81.0 | `infra/terraform/` |
| Deployment orchestration | Protected CI/CD | GitHub Actions and Entra OIDC | `.github/workflows/` |
| ML lifecycle | Portable lifecycle with local and Azure adapters | Python, local container, Azure ML CLI v2 YAML | `data-science/`, `scripts/run_local_lifecycle.py`, `mlops/azureml/` |
| Evidence | Append-only project evidence | Azure Blob plus GitHub artifacts | `scripts/emit_evidence.py`, `scripts/plan_artifact.py` |

No Azure Developer CLI configuration exists, and none will be introduced. Bicep, Foundry, Search, Databricks, online serving, monitoring, retraining, Test, and Prod remain outside this deployment.

## 4. Recipe selection

**Selected:** Pure Terraform through the existing protected GitHub saved-plan workflow.

**Rationale:** The factory has an established immutable-plan contract that binds product source, generation identity, platform package, tenant, subscription, backend, remote state, Terraform/provider versions, action summary, and human-reviewed digests. Adding azd would create a second orchestration authority and would violate the locked R1 Terraform ownership contract. The deployment plan satisfies governance prerequisites but does not replace or wrap Terraform execution.

## 5. Architecture and ownership

| Component | Azure service or external owner | Ownership and purpose |
|---|---|---|
| Environment boundary | Existing `rg-azure-ai-ml-ops-dev` | Administrator-created bootstrap prerequisite; workload Terraform creates resources inside it |
| Remote state | Existing `stazmlops0001devtf/azure-ai-ml-ops-r1` | Bootstrap-owned backend; workload key `azure-ai-ml-ops-dev.tfstate` |
| Workspace | Azure Machine Learning | Project-owned, system-assigned identity, identity-based storage access |
| Storage and evidence | Azure Storage | Project-owned; Shared Key disabled; private evidence container and retention policy |
| Secrets boundary | Azure Key Vault | Project-owned; RBAC authorization; no generated secrets |
| Observability | Log Analytics and Application Insights | Project-owned Dev observability |
| Compute | None in the default local-first profile | Azure training and batch compute are independent opt-ins; an enabled Dev cluster has minimum zero and maximum one node; serverless training creates no persistent cluster |
| Compute identity | Conditional user-assigned managed identity | Project-owned and created only when an Azure ML cluster is enabled; storage data access for ML operations |
| Workflow identity | Existing Entra OIDC principal | Bootstrap-owned; scoped workload deployment and project-storage evidence access |
| RBAC | Two base Storage Blob Data Contributor assignments, plus one conditional compute assignment | Workload Terraform; exact storage scope for workspace and workflow principals, and for the project compute principal only when cluster compute is enabled |

The default Dev execution sequence is `prepare -> train -> evaluate -> package -> score -> local evidence`. It invokes the same generated lifecycle scripts, schemas, metric and promotion policy used by the Azure adapter. A local result is not evidence of Azure ML job submission, managed identity, lineage, registration, endpoint deployment, or batch execution.

Cloud policy is explicit intent. Training may independently select Azure ML serverless or a scale-to-zero cluster. Batch may independently select a scale-to-zero cluster. No cloud fallback has an implicit VM SKU, and the factory must never replace an unavailable SKU. Every enabled Dev cluster has `max_instances = 1`. Workflow dispatch requires an explicit cost-aware authorization input before a charged compute operation can start.

The one-resource/one-IaC-owner rule remains mandatory. Workload Terraform must not manage bootstrap state, the environment resource group, GitHub repository/environment, Entra application, or federated credential.

## 6. Provisioning-limit checklist

The prior quota evidence is historical evidence for the rejected `Standard_D4s_v5` candidate. The replacement local-first base plan requests no Azure ML compute cluster or compute-family vCPU capacity. If cloud compute is later enabled, SKU availability and quota must be rediscovered read-only for the exact explicit instance type before planning and again before execution.

| Resource or quota | Planned | Current | Total after deployment | Limit or available capacity | Evidence and result |
|---|---:|---:|---:|---:|---|
| Azure ML clusters | 0 by default | 5 | 5 | 200 | Local-first base profile; no compute cluster requested |
| Azure ML total dedicated vCPUs | 0 by default | 4 | 4 | 350 | Charged cloud execution disabled by default |
| VM-family vCPUs | 0 by default | Not applicable | Not applicable | Explicit-SKU discovery required when enabled | No default or silent replacement SKU |
| Azure ML workspaces | 1 | 2 | 3 | No count quota exposed by `az quota` | ARM inventory plus successful provider plan; pass |
| Storage accounts | 1 | 4 | 5 | 250 per region/subscription default | ARM inventory and Azure service limits; pass |
| Key Vaults | 1 | 2 | 3 | No count quota exposed | ARM inventory plus successful provider plan; pass |
| Log Analytics workspaces | 1 | 0 | 1 | No applicable count quota surfaced | ARM inventory plus successful provider plan; pass |
| Application Insights components | 1 | 2 | 3 | No component-count quota surfaced | ARM inventory; workspace-based component; pass |
| User-assigned managed identities | 0 by default | 2 | 2 | No count quota exposed | Conditional on enabled cluster compute |
| Azure role assignments | 2 by default | 58 | 60 | 4,000 per subscription | Conditional compute role omitted with cluster compute |
| Evidence container and storage policy | 2 child resources | 0 in new account | 2 | Bound to the single planned storage account | No independent subscription quota; pass |

**Status:** The local-first base profile declares no cloud compute capacity. Exact-SKU availability and quota are unresolved by design until a cloud fallback is explicitly configured.

## 7. Execution checklist

### Phase 1: Planning

- [x] Analyze the workspace in MODIFY mode.
- [x] Confirm the existing manifest subscription, tenant, and location.
- [x] Scan the factory, generated Terraform, workflows, and evidence contracts.
- [x] Select the pure Terraform recipe and preserve existing ownership.
- [x] Query subscription policies, resource inventory, and quotas read-only.
- [x] Define architecture, exclusions, authorization, and stop conditions.
- [x] Obtain approval of this finalized deployment plan.

### Phase 2: Factory integration

- [x] Add strict execution and cost-policy contracts with local-first defaults and independent Azure training/batch fallbacks.
- [x] Remove the implicit `Standard_D4s_v5` and four-node defaults.
- [x] Generate cluster, compute identity, compute RBAC, outputs, and cloud workflows only when explicitly enabled.
- [x] Add a local runner and pinned container that invoke the same lifecycle implementation as Azure ML.
- [x] Require an explicit cost-aware workflow authorization before cloud compute execution.
- [x] Update deterministic provenance, governance documentation, and tests.
- [x] Run platform and generated-project conformance, then set the plan `Ready for Validation`.

### Phase 3: Validation and publication

- [ ] All replacement validation checks pass:
  - [x] Terraform is installed.
  - [x] Azure CLI is installed and authenticated to the declared subscription.
  - [x] Generated Terraform initializes with the backend disabled and the checked-in lock file.
  - [x] Generated Terraform formatting passes.
  - [x] Generated Terraform validation passes.
  - [x] Saved Terraform planning is prohibited during factory validation and deferred to protected product `main` in Phase 4.
  - [x] Remote state identity binding is deferred to Phase 4; the current backend container and state blob passed read-only data-plane visibility checks.
  - [x] No unresolved Go-style environment template variables exist.
  - [x] No `main.tfvars.json` file is generated; JSON syntax validation is not applicable.
  - [x] Read-only Azure policy, inventory, role-assignment, SKU, and quota checks pass.
- [ ] Complete the Azure validation workflow for the local-first candidate.
- [ ] Mark the generated product plan `Validated` only through that workflow.
- [ ] Build two byte-identical wheels and record the exact digest.
- [ ] Regenerate two byte-identical product trees.
- [ ] Publish through protected platform and product PR/CI workflows.

### Phase 4: Replacement saved-plan gate

- [x] Record run `31632608556` as `superseded_before_apply`, mandatory deployment-governance artifact absent, no resources mutated.
- [x] Retire the unpublished compute-bound generation `sha256:54b4af8c...d7b6c0` as blocked before publication because its implicit SKU was unavailable.
- [x] Produce a new saved Terraform plan from protected product `main` only.
- [x] Derive and review the exact create count from the replacement local-first Terraform graph; require zero update, replacement, or destroy actions.
- [x] Reproduce the sanitized JSON with Terraform 1.10.0.
- [x] Rebind and recheck backend identity plus state lineage, serial, and content digest.
- [ ] Request new deliberate, digest-bound owner authorization.
- [x] Stop before apply.

### Phase 4 result: 2026-08-13

Regenerated from platform commit `ef56abc1a8af0b18c8487763ae85267b738144ec` (ADR 0010 local-first compute). Two independent clean-room platform wheel builds matched (`sha256:a107e628d415c1281a194f7dba86dbc200ae126c180a59b67bfa372ea092248f`, reproducible only after pinning `SOURCE_DATE_EPOCH` to the commit timestamp — `setuptools`/`wheel` otherwise embed wall-clock build time in `dist-info` and break byte-for-byte reproducibility). Two independent `aiml-scaffold generate` runs matched (`generated_files_digest sha256:e3f14de3bd67f1384c185e6f3432df4721f835dc3cb9c99f6b11eef475ee9a82`; `manifest_digest sha256:c01e4c7a6434584cbbebd1fac2ae2f2b92de9854d98d4f6322d1b2e944f8945d`, confirmed identical to the last real R1 candidate's manifest digest, independently corroborating the reconstructed manifest).

| Evidence | Sanitized result |
|---|---|
| Product publication | PR `rubyrayjuntos/azure-aiml-ops#8` (regeneration), merge commit `4c422adf6d7cc50cf92c206f7873a7e950389176`; PR CI `31647605675` and post-merge CI `31654411635` passed |
| Governance publication | PR `rubyrayjuntos/azure-aiml-ops#9` (Azure validation workflow evidence, status set to `Validated`), merge commit `432663a9f0db85cece92db6e9bebb22acf5f5e59`; PR CI `31654848431` and post-merge CI `31654969743` passed |
| Authenticated doctor | `overall_status: warning`; every check passed except `active_identity_match` (active identity is the operator's user, not the GitHub deployment identity — expected, not a failure); compute SKU/quota checks are `not_applicable` because the local-first profile requests zero Azure compute |
| First plan attempt | Run `31654533527` failed fast and safely: `plan artifact validation failed: deployment plan status is not Validated` — the generated `.azure/deployment-plan.md` intentionally starts at `Planning`; no plan or apply occurred |
| Saved plan | Run `31655061017`, attempt `1`, source commit `432663a9f0db85cece92db6e9bebb22acf5f5e59`; exact six-file artifact `terraform-plan-dev-31655061017-1` |
| Plan digests | Binary `sha256:e87c41525a021d528169abd96456975fa6424b8018c4a8cc9a72a500aaf9a998`; sanitized JSON `sha256:ef68a2a1c52e4dfbfd0a907a30c7433925f06d4bfb7bc555db7cd3e4cabaf442` |
| Independent representation | Downloaded the artifact locally; initialized Terraform `1.10.0` against the live backend under the operator's own Entra identity; `terraform show -json` plus the platform's own `_sanitize` function re-derived a byte-identical sanitized JSON; `scripts/plan_artifact.py verify` passed against the live current-state snapshot |
| State binding | Backend lineage `6ee99d75-b936-96fd-17d6-da83ebe82ed7`, serial `1`, empty state (no prior R1 apply); matched the plan's recorded pre-plan snapshot |
| Action summary | 9 creates; 0 updates, replacements, deletes, reads, or no-ops — `azurerm_application_insights.this`, `azurerm_key_vault.this`, `azurerm_log_analytics_workspace.this`, `azurerm_machine_learning_workspace.this`, `azurerm_role_assignment.workflow_storage`, `azurerm_role_assignment.workspace_storage`, `azurerm_storage_account.this`, `azurerm_storage_container.evidence`, `azurerm_storage_management_policy.evidence` |
| Identity and RBAC | Workspace `SystemAssigned`; default storage access `Identity`; both role assignments grant `Storage Blob Data Contributor` scoped to the project storage account only; no Owner, no subscription-level scope, no unrelated role; no compute UAMI (local-first profile requests zero Azure compute) |
| Storage posture | `shared_access_key_enabled: false`; `public_network_access_enabled: true` (known Dev-only posture; production private-network conformance is out of scope) |
| Boundary review | No bootstrap resource, subscription Owner, ACR, endpoint, Bicep resource, or resource-group overlap; all resources target `rg-azure-ai-ml-ops-dev` |
| Apply | Not dispatched and not authorized |

Disposition: `saved_plan_review_passed_apply_not_authorized`.

### Apply attempt and correction: 2026-08-13

The owner gave deliberate, digest-bound authorization naming plan run `31655061017` attempt `1` and sanitized-JSON digest `sha256:ef68a2a1c52e4dfbfd0a907a30c7433925f06d4bfb7bc555db7cd3e4cabaf442`. Apply run [31657449816](https://github.com/rubyrayjuntos/azure-aiml-ops/actions/runs/31657449816) created `azurerm_log_analytics_workspace.this`, `azurerm_application_insights.this`, and `azurerm_key_vault.this`, then failed creating `azurerm_storage_account.this`: the AzureRM provider's post-creation data-plane readiness poll defaulted to key-based auth against an account with Shared Key correctly disabled (`403 KeyBasedAuthenticationNotPermitted`). Terraform state retained all three successful resources plus the storage account, which it marked tainted. No resource was destroyed; no automatic remediation was attempted.

Root cause: the generated `provider "azurerm" {}` block lacked `storage_use_azuread = true`. Fixed in platform commit `b36beac93db570310a7ea7e920eb65e70371ceb3`. Regenerated, republished (PR #10, merge `cbc5362b20b317424424209ba3131475957deea9`), and revalidated (PR #11, merge `b4d6aaf6ff975f4ce9e6db3b78f878d7a5828d95`) through the same protected PR/CI and Azure-validation-workflow sequence as the original candidate.

| Evidence | Sanitized result |
|---|---|
| Saved plan | Run `31659934644`, attempt `1`, source commit `b4d6aaf6ff975f4ce9e6db3b78f878d7a5828d95` |
| Plan digests | Binary `sha256:6d228c54e8d78fa87a9da918bce7420a51110de7df5c05df1244ab334db37160`; sanitized JSON `sha256:9c190f51a377cb9ab8e0ac14210838594cf4bb33aefd4883ee86ffb2caa95a2d` |
| Independent representation | Re-derived locally with Terraform `1.10.0` against live backend state; byte-identical sanitized JSON; `scripts/plan_artifact.py verify` passed against the live current-state snapshot |
| Action summary | 3 no-op (`azurerm_application_insights.this`, `azurerm_key_vault.this`, `azurerm_log_analytics_workspace.this`); 5 create (`azurerm_machine_learning_workspace.this`, both role assignments, `azurerm_storage_container.evidence`, `azurerm_storage_management_policy.evidence`); 1 replace (`azurerm_storage_account.this`) |
| Replace review | Terraform's own reason: `is tainted, so must be replaced` — a direct consequence of the prior partial-apply failure, not config drift. `name` is unchanged (`stazureaimlopscffddc57`); the account holds no data and no dependent resource was ever created against it |
| Owner review | Reported the deviation from the "zero replacement" bar explicitly before proceeding; owner reviewed the tainted-resource explanation and authorized apply of this exact plan run/digest |
| Apply | Run [31660270459](https://github.com/rubyrayjuntos/azure-aiml-ops/actions/runs/31660270459): the storage account destroyed and recreated cleanly, then the evidence container, lifecycle policy, and ML workspace all created successfully. Failed on two further findings (below). No resource was destroyed by this failure; the workspace and its dependencies were retained |

**Second correction.** Run `31660270459` surfaced two further findings, both diagnosed from live logs and role-assignment queries before any further action:

1. `azurerm_role_assignment.workspace_storage` failed with `409 RoleAssignmentExists`. Confirmed live (`az role assignment list` on the storage account) that `Microsoft.MachineLearningServices` auto-grants the workspace's system-assigned identity `Storage Blob Data Contributor` (and `Storage File Data Privileged Contributor`) on its default storage account whenever `storage_account_access_type` is `"Identity"`. The explicit Terraform-managed role assignment for the same principal/role/scope was redundant and conflicted with the auto-provisioned one.
2. Evidence recording failed with `AuthorizationPermissionMismatch` roughly 10 seconds after the `workflow_storage` role assignment was created — an RBAC propagation-delay race, not a real permission gap.

Fixed in platform commit `ad90be40efe1c9b530c8a2de733e591795b669d9`: removed the redundant role assignment and its output; added retry-with-backoff (5/10/20/40/40s) to the evidence blob write. Regenerated, republished (PR #12, merge `02ddc69e43486556d826652a0aec60e3c1c7f587`), and revalidated (PR #13, merge `ae9e185f19a22c7fe5834df4271ba62b36c97c3f`).

| Evidence | Sanitized result |
|---|---|
| Saved plan | Run `31661241595`, attempt `1`, source commit `ae9e185f19a22c7fe5834df4271ba62b36c97c3f` |
| Action summary | 7 no-op; 1 replace (`azurerm_role_assignment.workflow_storage`, `replace_because_cannot_update`) |
| Replace review | `role_definition_id` recorded at creation used the subscription-scoped ARM path; `data.azurerm_role_definition` resolved the same built-in role to the global path on this plan — same role, different immutable path string, not config drift |
| Owner review | Reported as lower-risk than the storage-account replace (role assignment recreation has no functional effect); owner recommended fixing before another apply rather than accepting a recurring replace |
| Apply | Not dispatched; fixed instead (below) |

**Third correction.** Fixed in platform commit `051432a904fc455925af641fc1e155b1dd8cfb66`: removed the `data "azurerm_role_definition" "blob_contributor"` data source entirely and switched both role assignments to `role_definition_name = "Storage Blob Data Contributor"`, sidestepping the ARM path-format ambiguity. Verified the rendered Terraform is byte-identical to `terraform fmt`'s output before publishing. Regenerated, republished (PR #14, merge `fb103f23d88b3c828cc48ab4093f85d9b3d085c9`), and revalidated (PR #15, merge `708c79a310de4f126148488431618e18bd038beb`).

| Evidence | Sanitized result |
|---|---|
| Saved plan | Run `31662465677`, attempt `1`, source commit `708c79a310de4f126148488431618e18bd038beb` |
| Plan digests | Binary `sha256:99eb564ce4c745f0393e937696aa8f5f1356b9a28233d8edf6a047c3cb6aff38`; sanitized JSON `sha256:bf01ba976627f5d80475813b63e1b3d1aefe81e9ae4afc21b12df517a95acd87` |
| Independent representation | Re-derived locally with Terraform `1.10.0` against live backend state; byte-identical sanitized JSON; `scripts/plan_artifact.py verify` passed against the live current-state snapshot |
| Action summary | **8 no-op; 0 create, replace, update, or delete** |
| State binding | Backend lineage `6ee99d75-b936-96fd-17d6-da83ebe82ed7`, serial `6`, unchanged since the second apply attempt |
| Apply | Not dispatched; awaiting owner authorization |

**Apply.** Owner gave deliberate, digest-bound authorization naming plan run `31662465677` attempt `1` and sanitized-JSON digest `sha256:bf01ba976627f5d80475813b63e1b3d1aefe81e9ae4afc21b12df517a95acd87` via direct instruction on 2026-08-13. Dispatched as run [31663570921](https://github.com/rubyrayjuntos/azure-aiml-ops/actions/runs/31663570921).

| Evidence | Sanitized result |
|---|---|
| Outcome | `success`; every step passed, including `Verify applied identity and RBAC graph` and `Record infrastructure evidence` — both of which failed on every prior attempt and ran clean for the first time here |
| Duration | Started `2026-08-13T03:19:46Z`, completed `2026-08-13T03:19:59Z` — a 13-second no-op apply, consistent with the plan's own 8-no-op/0-change summary |
| Post-apply state | `terraform state pull`: serial `7`, same lineage `6ee99d75-b936-96fd-17d6-da83ebe82ed7`; 8 tracked resources, no taint, no orphaned data source |
| Identity/RBAC verification | Workspace principal ID matched the live ARM resource (`afa3648e-6b75-4394-ae9a-f290813a6946`); workflow role assignment confirmed unique `Storage Blob Data Contributor` at the storage scope; workspace resource-group `Azure AI Administrator` assignment confirmed |
| Evidence recording | `emit_evidence.py` succeeded (retry/backoff not needed this time — no fresh role assignment in this apply to race against); local re-verification blocked by 403 under the operator's own identity, which correctly has no RBAC on the project storage account (only the workflow and workspace identities do) — this is the intended least-privilege posture, not a gap |
| Authorization record | `apply-authorization-and-result.json`: `authorized_by: rubyrayjuntos`, `outcome: success`, full digest/commit/generation-ID chain intact |

Disposition: `apply_succeeded`. R1 Dev now has a live Azure ML workspace, identity-based storage, evidence pipeline, Key Vault, and observability stack. Azure ML training, evaluation, model registration, challenger/champion promotion, batch endpoint deployment, and monitoring remain entirely unexercised and unauthorized by this plan — that is the next, separately-gated phase.

## 8. Validation proof

The approved Azure validation workflow executed locally and with authenticated read-only Azure access. Terraform planning, state locking/writes, apply, and Azure ML workload operations were deliberately not exercised.

| Check | Command | Result | Timestamp |
|---|---|---|---|
| Platform contracts | `python -m pytest -q` | Passed, 112 tests | 2026-08-12T21:02:00Z |
| Python lint and diff hygiene | `python -m ruff check .`; `git diff --check` | Passed | 2026-08-12T20:36:58Z |
| Deterministic generation | Two independent `aiml-scaffold generate` executions plus tree comparison and receipt verification | Passed; byte-identical source trees | 2026-08-12T20:36:58Z |
| Generated repository | Generated tests, Ruff, YAML parsing, Actionlint, scenario scan, and offline doctor | Passed; 8 tests; dedicated secret-scanner binary unavailable, credential rejection vectors passed in platform suite | 2026-08-12T20:36:58Z |
| Terraform static validation | `terraform fmt -check -recursive`; `terraform init -backend=false -lockfile=readonly`; `terraform validate` | Passed with AzureRM 4.81.0; no plan or state mutation | 2026-08-12T20:36:58Z |
| Package build | Scratch-source wheel build and ZIP content inspection | Passed; hidden deployment-plan template included and runtime cache files excluded | 2026-08-12T20:36:58Z |
| Azure context and policy | `az account show`; subscription policy assignment query | Passed; intended tenant/subscription; one enforced Security Center default assignment | 2026-08-12T20:36:58Z |
| Backend read boundary | Storage management-plane lookup, container show, Entra blob list | Passed; Shared Key disabled; private container; state blob visible; no write/lock | 2026-08-12T20:36:58Z |
| Capacity and inventory | Azure ML quota/usage, VM usage/SKU, Resource Graph inventory, role-assignment count | Passed; 32 requested DSv5 vCPUs fit within 65; three planned roles fit within current count 58 and subscription limit | 2026-08-12T20:36:58Z |
| Static RBAC | Terraform principal/role/scope/purpose/dependency review | Initial omission found and corrected; workspace, compute, and workflow principals now each receive exact-storage `Storage Blob Data Contributor` (**superseded 2026-08-13 — see note below the Role assignment verification section**) | 2026-08-12T20:36:58Z |
| Installed-wheel product conformance | Generate with the clean reproducible wheel, then run generated tests | Failed safely: package-data omitted `scripts/emit_evidence.py.j2`; wheel `sha256:41f429c4f1c9bf73247a3440e39963382c3519e9c7e883070ed254eeff370864` and generation `sha256:ccc9517a2a97f80df8b4c8403bc226d48bb5fa843b745d5e3e5b6f6196fabec6` invalidated before publication or Azure access | 2026-08-12T20:45:00Z |
| Post-install provenance | Failed editable install under unsupported local Python 3.13, followed by receipt verification | Found and corrected false source-drift detection from setuptools-created `*.egg-info`; verifier now excludes only recognized build/runtime paths and retains all tracked-source checks | 2026-08-12T20:48:00Z |
| Corrected installed-wheel conformance | Clean scratch build, isolated wheel install, product generation, 8 generated tests, Ruff, YAML, Actionlint, Terraform init/validate, receipt checks before and after synthetic build metadata | Passed; evidence writer and deployment plan present; no runtime cache included; Python 3.12 dependency installation remains protected CI authority because local interpreter is 3.13 | 2026-08-12T20:48:31Z |
| Product authenticated doctor | Exact replacement generation with intended identity identifiers | Required context/backend/OIDC/RBAC checks passed, but supported subscription-aware SKU discovery reports `Standard_D4s_v5` restricted in East US; product validation and planning stopped | 2026-08-12T20:58:00Z |

**Validated by:** Repeated Azure validation workflow after subscription-aware doctor correction.

## Role assignment verification

- **Status:** Corrected locally; full regenerated validation pending.
- **Identities checked:** Azure ML workspace system-assigned identity, project compute user-assigned identity, and bootstrap-owned GitHub workflow service principal.
- **Roles confirmed:** `Storage Blob Data Contributor` on the exact project storage account for all three identities.
- **Purpose:** Workspace identity-based default-storage access; compute model/MLflow input and output; workflow evidence publication.
- **Dependency:** Workspace and compute assignments reference Terraform-created identity principal IDs; workflow assignment uses the manifest-declared object ID. All scopes reference the Terraform-created storage resource.
- **Excluded roles:** No subscription-level role, Owner, broad Contributor, Key Vault data role, ACR role, or unrelated service permission is introduced.
- **Validation finding:** Static role verification found that the prior template omitted the required workspace-storage data-plane assignment. The correction changes the expected create-only plan from 12 to 13 resources and requires a new candidate and saved plan.

**Superseded 2026-08-13.** This entire section described a static (never live-verified) assumption: that the workspace identity's storage RBAC had to be an explicit Terraform-managed `azurerm_role_assignment`, alongside compute and workflow. Live apply run `31660270459` proved that assumption wrong — `Microsoft.MachineLearningServices` auto-grants the workspace's system-assigned identity `Storage Blob Data Contributor` (and `Storage File Data Privileged Contributor`) on its default storage account whenever `storage_account_access_type` is `"Identity"`; the explicit Terraform-managed duplicate conflicted with it (`409 RoleAssignmentExists`, confirmed live via `az role assignment list`). It was removed in platform commit `ad90be40efe1c9b530c8a2de733e591795b669d9`. In the current (local-first) architecture, Terraform manages only `workflow_storage`; the compute identity's role assignment exists solely behind the `compute_identity_required` flag, which the local-first Dev profile does not enable, so no compute role assignment is created by default either. The "12 to 13 resources" framing above no longer applies — see `## 6. Provisioning-limit checklist` and the Phase 4 apply-evidence sections for the resource counts and RBAC posture that actually shipped.

## 9. Files to generate or update

| File | Purpose | Planned state |
|---|---|---|
| `.azure/deployment-plan.md` | Workspace preparation and validation source of truth | Approved; validation pending |
| `src/aiml_scaffold/templates/azure_ml_batch/.azure/deployment-plan.md.j2` | Deterministic generated governance plan | Implemented locally |
| `src/aiml_scaffold/generator.py` | Explicit mutable-governance-path digest handling | Implemented locally |
| `src/aiml_scaffold/templates/azure_ml_batch/scripts/plan_artifact.py` | Saved-plan governance digest binding | Implemented locally |
| `tests/unit/test_generator.py` | Governance generation and provenance regression tests | Focused tests passing |
| `docs/decisions/0009-r1-deployment-plan-governance.md` | Governance ownership and digest ADR | Implemented locally |
| `docs/superpowers/plans/r1-dev-evidence-matrix.md` | Candidate retirement and replacement evidence | Prior plan retired; replacement pending |

## 10. Authorization and stop conditions

Any later apply authorization covers infrastructure creation only and explicitly excludes:

- replanning or replacement planning inside apply;
- bootstrap, GitHub, Entra, backend, or resource-group changes;
- training, model registration, endpoint deployment, batch jobs, or invocation;
- Test or Prod;
- unreviewed remediation or corrective Terraform changes.

Apply must stop before Terraform execution if any required filename, digest, source identity, generation identity, Azure context, backend identity, state lineage, state serial, or state content digest differs. A state serial or digest change invalidates the saved plan even when lineage is unchanged.

Failed deployment retains state, GitHub evidence, and any project-local evidence. No automatic destroy or replacement plan is permitted.

## 11. Next steps

Current phase: R1 Dev infrastructure apply is complete. After two apply attempts and three diagnosed-and-fixed findings (storage data-plane auth, redundant workspace RBAC plus an evidence-write RBAC-propagation race, and role-definition-ID path-format instability), apply run `31663570921` succeeded end to end — including the identity/RBAC verification and evidence-recording steps that failed on every prior attempt. All 8 resources (Log Analytics, Application Insights, Key Vault, storage account, evidence container, evidence lifecycle policy, ML workspace, workflow role assignment) are live and correctly configured. Azure ML training, evaluation, model registration, challenger/champion promotion, batch endpoint deployment, and monitoring remain entirely unexercised.

1. ~~Implement and statically validate the local-first compute contract.~~ Done.
2. ~~Publish through protected platform and product PR/CI and regenerate deterministically.~~ Done.
3. ~~Produce and review a saved Terraform plan from protected product `main`.~~ Done (run `31662465677`, fourth candidate, 8 no-op / 0 changes).
4. ~~Correct every finding surfaced by live apply attempts rather than leaving a known-recurring defect.~~ Done (three corrections, each republished and revalidated).
5. ~~Obtain deliberate, digest-bound owner authorization and apply the clean plan.~~ Done (run `31663570921`, `outcome: success`).
6. ~~Run the authenticated doctor once more against the applied infrastructure.~~ Done, 2026-08-13. `overall_status: warning`, same single expected `active_identity_match` warning as every prior run. `backend_state_write_and_lock` and `oidc_token_exchange` remain `not_exercised` by the doctor tool itself (both require a live write/OIDC-issuing context the read-only CLI cannot create) but both are independently proven by the apply run's own success: `31663570921` performed a real state write/lock (serial 6 → 7) and every workflow this session authenticated via real OIDC token exchange to `azure/login`.

### Gate 1 workload evidence: paused on quota, 2026-08-13

Owner authorized the full Gate 1 sequence (healthy training run, immutable registration, losing challenger, winning challenger, conditional batch redeployment, invocation, monitoring/drift proof) in one pass. Before spending anything, checked live SKU availability the same way `doctor`'s `compute_sku_availability` check does: `az vm list-skus --location <region> --size <sku> --all --subscription 5b452321-32fd-4b1c-8bbf-6d69a5a587ad --output json`.

| Evidence | Sanitized result |
|---|---|
| SKUs checked | `Standard_D4s_v5`, `Standard_DS3_v2`, `Standard_D2s_v3`, `Standard_D2s_v5`, `Standard_F2s_v2`, `Standard_DS2_v2` |
| Regions checked | `eastus`, `eastus2` |
| Result | All 6 SKUs restricted in both regions checked, reason `NotAvailableForSubscription` (both `Location` and `Zone` restriction entries) |
| Quota confirmation | `az vm list-usage --location eastus`: `Dedicated vCPUs` shows `0` current / **`0` limit** — a hard zero ceiling, distinct from and gating underneath the healthy-looking per-family quotas (e.g. `Standard D Family vCPUs: 0/65`) that never actually become usable while the dedicated ceiling is zero |
| Low-priority headroom | `Total Regional Low-priority vCPUs: 0/3` shows nonzero limit, but `NotAvailableForSubscription` restrictions apply at the SKU/location level in the ARM compute-provider catalog and are not tier-specific, so a spot/low-priority allocation of the same restricted SKUs is expected to fail identically — not attempted live, since the owner chose to pause rather than spend a cycle confirming a near-certain failure |
| Relationship to prior evidence | Matches the R1 Dev evidence matrix's `2026-08-12T20:58:00Z` finding (`Standard_D4s_v5` restricted in East US) that originally motivated the local-first pivot (ADR 0010). This is the same subscription-level restriction, not a template or SKU-choice defect — confirmed here across five additional SKUs and a second region |
| Owner decision | Pause Gate 1 until Azure lifts the Dedicated vCPU restriction (support request required) or a subscription without this restriction is available. No manifest change, plan, or apply was attempted for cloud compute; the applied R1 Dev infrastructure (8 resources, local-first) is unaffected and remains exactly as recorded above |

**What resolves this:** a Microsoft support request for a Dedicated vCPU quota increase on subscription `5b452321-32fd-4b1c-8bbf-6d69a5a587ad` in `eastus` (or another target region) — Azure Portal → Support + troubleshooting → New support request → Service and subscription limits (quotas) → quota type "Compute-VM (cores-vCPUs) subscription limit increases". Given the local-first policy's own `max_instances: 1` ceiling, a minimal request (a handful of vCPUs in one small family, e.g. `Standard D Family` or `DSv3 Family`) should be sufficient to unblock Gate 1 — no need to request the full 65-vCPU family ceiling already nominally allowed.

### Gate 1 workload evidence: resumed, 2026-08-14

Owner submitted a quota-increase support request (case `2608140040007160`) via the Azure Portal self-service flow. Microsoft's response: approved, `Total Regional vCPUs` raised `65` → `73` in `eastus`. Before assuming this resolved the blocker, verified directly rather than taking the approval email at face value.

| Evidence | Sanitized result |
|---|---|
| Quota after approval | `az vm list-usage --location eastus`: `Total Regional vCPUs` now `0/73` (was `0/65`); **`Dedicated vCPUs` unchanged at `0/0`** |
| SKU catalog re-check | `az vm list-skus --location eastus --size Standard_D2s_v3 --all`: still `NotAvailableForSubscription`, identical restriction entries to before the approval |
| Ad-hoc cluster-definition test | `az ml compute create` (dedicated tier, `min_instances=0`) against the live R1 Dev workspace **succeeded** — contradicts the SKU catalog result |
| Ad-hoc node-allocation test | Submitted a real job to force node allocation. Failed, but inconclusively: `targetNodeCount` stayed `0` (never attempted VM allocation) and the job failed at artifact-upload time with `AuthorizationPermissionMismatch` — the testing identity (operator's own Entra user) has no storage RBAC on the project account, by design (least-privilege). This test produced no evidence about compute quota either way, and both ad-hoc test resources were deleted after |
| Owner decision | Two static signals disagree (SKU catalog: still blocked; cluster-definition creation: now succeeds) and ad-hoc CLI testing can't resolve it cleanly, since the operator identity deliberately lacks the RBAC needed to run a real job. Rather than a third ad-hoc test with temporarily-elevated permissions (rejected, to avoid a permissions change outside the reviewed pipeline), owner authorized resuming Gate 1 through the actual reviewed pipeline: enable cloud compute in the manifest, full plan/apply/dispatch cycle, using the deployment identity that already has correct RBAC from the Terraform build |

**Regeneration.** Manifest-only change (no platform code change; reused platform commit `051432a904fc455925af641fc1e155b1dd8cfb66`, wheel `sha256:c8a73fac24186f987c7b9341a0068645c85ba1dd828ea26100eb3af26a14704b`). Enabled `execution.training`/`execution.batch` cloud fallback: `Standard_D2s_v3`, dedicated tier, scale-to-zero, max 1 node each. Published (PR #16, merge `2783ff79c0ca9840c704a3f431c4a5dae6a83c9c`) and validated (PR #17, merge `a6dd16cb5293cd913500e922b57e997645cc5e19`) through the same protected PR/CI and Azure-validation-workflow sequence as every prior candidate — this time with one check left honestly failing rather than waived, since it's the exact thing under test.

| Evidence | Sanitized result |
|---|---|
| Authenticated doctor | `overall_status: failed` — `compute_sku_availability` and `compute_quota_sufficiency` both fail (same `NotAvailableForSubscription` result as the direct CLI check); every other check passed, including the expected `active_identity_match` warning |
| Saved plan | Run `31839827041`, attempt `1`, source commit `a6dd16cb5293cd913500e922b57e997645cc5e19` |
| Plan digests | Binary `sha256:eeb608bcc0778ecb30d2b815081c89635a7c0f118c3e3846008807d825bc93a7`; sanitized JSON `sha256:f55dd6239ac5292c2f226511a8ddf7de759b6d506fa5a6840a6c209b7d68acea` |
| Independent representation | Re-derived locally with Terraform `1.10.0` against live backend state; byte-identical sanitized JSON; `scripts/plan_artifact.py verify` passed against the live current-state snapshot |
| Action summary | 8 no-op (all previously-applied resources unchanged); 4 create: `azurerm_user_assigned_identity.compute`, `azurerm_role_assignment.compute_storage` (`Storage Blob Data Contributor` by name, scoped to the project storage account), `azurerm_machine_learning_compute_cluster.training`, `azurerm_machine_learning_compute_cluster.batch` |
| Apply | Not dispatched; awaiting owner authorization. This plan is expected to either (a) apply cleanly, proving the quota fix actually works for cluster *creation* — matching the ad-hoc test — or (b) fail at apply time on VM provisioning, matching the SKU catalog. Either outcome is real evidence; the subsequent `train.yml` dispatch against real workspace RBAC is what actually answers whether a node can run a job |

Disposition: `saved_plan_review_passed_apply_not_authorized`.
7. Begin the separately-gated Azure ML workload evidence sequence: training, evaluation, immutable model registration, declared retraining dataset, winning/losing challenger branches, conditional batch redeployment, and production-monitoring proof. None of that is authorized by this plan — each step needs its own explicit authorization, matching the R1 Dev clean-room evidence matrix.

## Documentation changelog

| Version | Created | Modified | Who | Notes |
|---|---|---|---|---|
| 2.4.0 | 2026-08-13 | 2026-08-13 | Ray Swan / Claude | Applied the clean saved plan (run `31662465677`, owner-authorized). Apply run `31663570921` succeeded end to end in 13 seconds (8 no-op, 0 changes), including the identity/RBAC verification and evidence-recording steps that failed on every prior attempt. R1 Dev infrastructure (Log Analytics, Application Insights, Key Vault, storage account with identity-based access, evidence container and lifecycle policy, ML workspace, workflow RBAC) is now live. Azure ML workload lifecycle (training/registration/challenger/redeploy/monitoring) remains entirely unexercised and separately gated. |
| 2.3.0 | 2026-08-13 | 2026-08-13 | Ray Swan / Claude | Applied run 31655061017 (owner-authorized): 3 of 9 resources created, then failed on storage data-plane auth. Diagnosed and fixed (storage_use_azuread); reapplied and failed again on redundant workspace RBAC plus an evidence-write RBAC-propagation race; diagnosed and fixed both (removed the redundant role assignment, added retry/backoff). A third finding — a spurious role-assignment replace from ARM role-definition-ID path-format ambiguity — was fixed before any further apply (role_definition_name). Final saved plan `31662465677` independently re-verified as 8 no-op, 0 changes. All 8 resources now live and correctly configured; apply of the clean plan remains unauthorized. |
| 2.2.0 | 2026-08-12 | 2026-08-13 | Ray Swan / Claude | Published the local-first regeneration and Azure validation workflow evidence through PRs #8/#9, produced saved Terraform plan `31655061017` (9 creates, 0 updates/replacements/deletes), and independently re-derived and verified the sanitized plan JSON with a locally-downloaded Terraform 1.10.0 against the live backend. Apply remains unauthorized. |
| 2.1.0 | 2026-08-12 | 2026-08-12 | Ray Swan / Codex | Completed local factory integration and advanced the owner-approved compute-policy change to Ready for Validation after 119 platform tests, deterministic generation, local/cloud generated conformance, Terraform validation, and local lifecycle proof. |
| 2.0.0 | 2026-08-12 | 2026-08-12 | Ray Swan / Codex | Reopened the plan for the authorized local-first compute-policy redesign; removed implicit SKU and four-node Dev defaults, made cloud training and batch independent opt-ins, and retained separate apply and charged-compute gates. |
| 1.9.0 | 2026-08-12 | 2026-08-12 | Ray Swan / Codex | Repeated platform validation successfully at 112 tests after making SKU discovery subscription-restriction-aware; product planning remains stopped. |
| 1.8.0 | 2026-08-12 | 2026-08-12 | Ray Swan / Codex | Recorded the authenticated product doctor SKU stop and corrected doctor to request complete subscription-aware SKU restriction metadata. |
| 1.7.0 | 2026-08-12 | 2026-08-12 | Ray Swan / Codex | Repeated the full Azure validation workflow successfully after installed-wheel and post-install provenance corrections; restored Validated status. |
| 1.6.0 | 2026-08-12 | 2026-08-12 | Ray Swan / Codex | Added installed-wheel evidence-writer packaging and standard build-metadata provenance exclusions after safe local negative tests. |
| 1.5.0 | 2026-08-12 | 2026-08-12 | Ray Swan / Codex | Reopened validation after installed-wheel generation omitted the evidence-writer template; invalidated the unpublished wheel and generation before Azure access. |
| 1.4.0 | 2026-08-12 | 2026-08-12 | Ray Swan / Codex | Completed the Azure validation workflow after resolving package-content and workspace-storage RBAC findings; assigned Validated status without planning or apply. |
| 1.3.0 | 2026-08-12 | 2026-08-12 | Ray Swan / Codex | Recorded the Azure validation role-review finding, added the required workspace default-storage assignment, and revised the replacement-plan expectation to 13 creates. |
| 1.2.0 | 2026-08-12 | 2026-08-12 | Ray Swan / Codex | Recorded locally conformant factory integration and advanced the approved plan to Ready for Validation. |
| 1.1.0 | 2026-08-12 | 2026-08-12 | Ray Swan / Codex | Recorded owner approval for Phases 2–4 while retaining the separate validation and apply gates. |
| 1.0.0 | 2026-08-12 | 2026-08-12 | Ray Swan / Codex | Finalized the Terraform-only deployment-governance integration plan, live capacity evidence, ownership boundaries, exclusions, and replacement-plan gate. |
| 0.1.0 | 2026-08-12 | 2026-08-12 | Ray Swan / Codex | Created the mandatory deployment-governance planning skeleton before implementation. |
