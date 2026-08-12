# R1 Azure ML Dev infrastructure deployment plan

> **Status:** Validated

Generated: 2026-08-12

## 1. Project overview

**Goal:** Add the mandatory deployment-governance artifact to every generated R1 Azure ML batch repository, validate a regenerated non-taxi Dev candidate, produce and review a new saved Terraform plan, and stop before apply for new digest-bound owner authorization.

**Path:** Modify the existing Azure-first AIML-SCAFFOLD factory and regenerate the product repository. Do not edit generated lifecycle source manually.

## 2. Requirements

| Attribute | Value |
|---|---|
| Classification | Development; R1 preview |
| Scale | Small; one product and one Dev environment |
| Budget | Cost-controlled; compute scales to zero |
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
| ML lifecycle | Batch ML workflow | Azure ML CLI v2 YAML and Python | `mlops/azureml/`, `data-science/` |
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
| Compute | Two Azure ML compute clusters | Project-owned training and batch clusters; `Standard_D4s_v5`, minimum zero, maximum four nodes each |
| Compute identity | User-assigned managed identity | Project-owned; storage data access for ML operations |
| Workflow identity | Existing Entra OIDC principal | Bootstrap-owned; scoped workload deployment and project-storage evidence access |
| RBAC | Three Storage Blob Data Contributor assignments | Workload Terraform; exact storage scope for workspace, compute, and workflow principals |

The one-resource/one-IaC-owner rule remains mandatory. Workload Terraform must not manage bootstrap state, the environment resource group, GitHub repository/environment, Entra application, or federated credential.

## 6. Provisioning-limit checklist

Read-only quota and inventory checks were run against East US on 2026-08-12.

| Resource or quota | Planned | Current | Total after deployment | Limit or available capacity | Evidence and result |
|---|---:|---:|---:|---:|---|
| Azure ML clusters | 2 | 5 | 7 | 200 | `az quota` `TotalClusters`; pass |
| Azure ML total dedicated vCPUs | 32 maximum | 4 | 36 | 350 | `az quota` `TotalDedicatedCores`; pass |
| Standard DSv5 family vCPUs | 32 maximum | 0 | 32 | 65 | `az vm list-usage` `standardDSv5Family`; pass |
| Azure ML workspaces | 1 | 2 | 3 | No count quota exposed by `az quota` | ARM inventory plus successful provider plan; pass |
| Storage accounts | 1 | 4 | 5 | 250 per region/subscription default | ARM inventory and Azure service limits; pass |
| Key Vaults | 1 | 2 | 3 | No count quota exposed | ARM inventory plus successful provider plan; pass |
| Log Analytics workspaces | 1 | 0 | 1 | No applicable count quota surfaced | ARM inventory plus successful provider plan; pass |
| Application Insights components | 1 | 2 | 3 | No component-count quota surfaced | ARM inventory; workspace-based component; pass |
| User-assigned managed identities | 1 | 2 | 3 | No count quota exposed | ARM inventory plus successful provider plan; pass |
| Azure role assignments | 3 | 58 | 61 | 4,000 per subscription | `az role assignment list --all`; pass |
| Evidence container and storage policy | 2 child resources | 0 in new account | 2 | Bound to the single planned storage account | No independent subscription quota; pass |

**Status:** All declared resources are within discovered limits. Maximum cluster capacity requires 32 DSv5 vCPUs; 33 remain after the declared maximum.

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

- [x] Add a deterministic initial `.azure/deployment-plan.md` to the generated template.
- [x] Treat deployment-plan status/proof and `.azure/validate-status.json` as mutable governance evidence bound by the product source commit and saved-plan digests, not as immutable generated-tree content.
- [x] Add tests for deterministic initial content, exclusions, validation prerequisites, and provenance boundaries.
- [x] Run platform tests, Ruff, generated repository tests, Actionlint, Terraform formatting/init/validation, and leakage checks.
- [x] Set the plan status to `Ready for Validation` before handing off to Azure validation.

### Phase 3: Validation and publication

- [x] All validation checks pass:
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
- [x] Complete the repeated Azure validation workflow after subscription-aware doctor correction.
- [ ] Mark the generated product plan `Validated` only through that workflow.
- [ ] Build two byte-identical wheels and record the exact digest.
- [ ] Regenerate two byte-identical product trees.
- [ ] Publish through protected platform and product PR/CI workflows.

### Phase 4: Replacement saved-plan gate

- [x] Record run `31632608556` as `superseded_before_apply`, mandatory deployment-governance artifact absent, no resources mutated.
- [ ] Produce a new saved Terraform plan from protected product `main` only.
- [ ] Require exactly 13 creates and zero update, replacement, or destroy actions. The thirteenth create is the validation-discovered workspace-storage data-role assignment.
- [ ] Reproduce the sanitized JSON with Terraform 1.10.0.
- [ ] Rebind and recheck backend identity plus state lineage, serial, and content digest.
- [ ] Request new deliberate, digest-bound owner authorization.
- [ ] Stop before apply.

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
| Static RBAC | Terraform principal/role/scope/purpose/dependency review | Initial omission found and corrected; workspace, compute, and workflow principals now each receive exact-storage `Storage Blob Data Contributor` | 2026-08-12T20:36:58Z |
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

Current phase: platform correction is validated; product progression is blocked on an explicit compute-SKU intent decision.

1. Implement the factory-generated governance artifact and validation workflow integration.
2. Complete the documented Azure validation workflow.
3. Stop again after replacement saved-plan review for new apply authorization.

## Documentation changelog

| Version | Created | Modified | Who | Notes |
|---|---|---|---|---|
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
