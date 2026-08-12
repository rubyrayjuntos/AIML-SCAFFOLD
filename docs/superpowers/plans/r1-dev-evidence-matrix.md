# R1 Dev clean-room evidence matrix

This matrix must be completed with independently verifiable Dev evidence. Creating the matrix does not authorize authenticated checks, Terraform operations, Azure ML jobs, endpoint changes, or resource destruction.

## Pre-apply

| Gate | Required evidence | Status |
|---|---|---|
| Explicit Azure context | Expected tenant and deployment subscription match the active CLI context | Confirmed for replacement candidate; invalidated candidate still contains placeholders |
| Real bootstrap references | Backend resource group, storage account, container, backend subscription, and cross-subscription policy result | Live: same-subscription backend and dedicated private `azure-ai-ml-ops-r1` container verified |
| Backend management plane | Storage account and state container are independently visible | Live: account and dedicated container independently verified |
| Backend data plane | Active CLI identity can list state blobs using Entra authentication; write and lock remain unexercised | Live: deployment principal listed the dedicated container through Entra in OIDC run `31621923439`; workload state write/lock remains unexercised |
| Environment-scoped OIDC | Application/client ID, principal/object ID, federated credential, exact environment roles, and no subscription Owner | Live: app/principal relationship, exact issuer/subject/audience, three scoped roles, and absence of Owner verified |
| OIDC token exchange | Actual GitHub workflow exchanges a token as the intended deployment identity | Passed live in run `31621923439`; client, object, and tenant claims matched the intended service principal |
| Authenticated doctor | Separate context, identity, backend, shared-key, OIDC configuration, RBAC, SKU, and quota results | Earlier candidate stopped before resource queries; bootstrap configuration is live, but replacement-candidate doctor remains pending |
| Active identity boundary | Local CLI identity is recorded separately from the intended GitHub deployment identity | Passed live: workflow token represented the intended service principal; the local CLI user was not used |
| Bootstrap plan | Approved prerequisites resolved into a verified infrastructure plan | Applied from reviewed saved plans; first apply preserved after GitHub reviewer-rule billing failure, then bounded corrective plan completed |
| Generation integrity | Manifest, plan, template, constraints, tree, and generation digests | Candidate receipt reverified before preflight |
| Generated conformance | Tests, Ruff, YAML, actionlint, Terraform validation, secret and scenario scans | Local proof only |
| Reviewed Terraform plan | Saved plan plus reviewer confirmation of resources, identities, roles, cost classes, and no Bicep overlap | Live: 13-create plan plus imported-container no-op; no updates, deletes, Owner role, or Bicep overlap |

## Apply and lifecycle

| Gate | Required evidence | Status |
|---|---|---|
| Terraform apply | Reviewed plan/apply identifiers with no unreviewed replacement or deletion | Bootstrap complete: 14 managed resources; zero changes or destroys; GitHub reviewer rule narrowed after provider returned billing-plan 422 |
| Clean second plan | No unexpected infrastructure drift | Passed live: Terraform detailed exit code `0`, no changes |
| Azure ML schema validation | Live workspace validation output | Pending authorization |
| Training and evaluation | Parent/child run IDs, immutable inputs, metrics, and promotion decision | Pending authorization |
| Conditional registration | Winning candidate version and losing candidate non-registration proof | Pending authorization |
| Explicit batch deployment | Endpoint, deployment, exact model version, and approval evidence | Pending authorization |
| Batch invocation | Invocation ID plus immutable input and output references | Pending authorization |
| Evidence integrity | Started/terminal events, receipt verification, local projection, and idempotent replay | Pending authorization |

## Negative acceptance

| Case | Expected result | Status |
|---|---|---|
| Challenger misses threshold | No registration | Pending |
| Missing or incorrect model version | Deployment blocked | Pending |
| Same event and digest repeated | Idempotent | Local proof only |
| Same identity with different content | Conflict | Local proof only |
| Same operation ID in different project/environment | Separate projections and receipts | Local proof only |
| Duplicate or conflicting receipt | Projection remains visible and reports `invalid`; no receipt is selected | Local proof only |
| Credential-bearing artifact URI | Rejected without echoing the URI | Local proof only |
| Altered generation receipt or provenance | Doctor stops before any authenticated query | Local proof only |
| Unauthorized evidence principal | Read/write denied | Pending authorization |
| Approval absent | Deployment prevented | Local contract proof: apply requires plan run/attempt, exact digest, target confirmation, and matching provenance; live workflow proof pending |
| Failed batch invocation | Failed terminal event and matching receipt | Pending authorization |
| Conflicting or post-terminal events | Projection remains visible and reports `invalid` | Local proof only |

No Test or Prod claim may inherit evidence from this Dev matrix.

## Saved workload plan review: 2026-08-12

| Evidence | Sanitized result |
|---|---|
| Platform source commit | `f928794` |
| Product source commit | `7ba0d8364dd9625b118e4afba92a485f865c6f71` on protected `main` |
| Generation ID | `sha256:f609615fd8706c19ee12a99a2d62732061e0d3f43dc172a44780bd836d87d027` |
| Reproducible wheel digest | `sha256:f596cb4f79b899651810796c814553cd9097a01345eac9132188ea72a0e08fbd` |
| Provider lock digest | `sha256:e23b20197002dae1c79db71736b06c67c7d4a7fb96b4d1433584c9aa2300c3f4`; AzureRM `4.81.0` |
| Terraform | `1.10.0` in GitHub and exact-version local JSON rendering |
| Backend | `stazmlops0001devtf` / `azure-ai-ml-ops-r1` / `azure-ai-ml-ops-dev.tfstate`; Entra/OIDC authentication |
| Plan workflow | Run `31623628917`, attempt `1`; succeeded without apply |
| Artifact | `terraform-plan-dev-31623628917-1`; binary plan and approval metadata retained for 30 days |
| Binary plan digest | `sha256:91e147dc5a5bd72f29c98cb48f8294a7cf31d395d9c033ad0dc63ebe3cb73b60` |
| Derived JSON digest | `sha256:4bed88eb1a345b393ad1ba27d23ef803a87d3e4649861f7720130a05e9124ab5`; locally rendered from the downloaded binary using Terraform `1.10.0` |
| Action summary | `10` creates, `0` updates, `0` replacements, `0` deletes |
| Ownership | Only project workload resources under `rg-azure-ai-ml-ops-dev`; no GitHub, Entra, backend-container, resource-group, or subscription-scoped ownership overlap |
| Compute posture | Training and batch clusters use `Standard_D4s_v5`, minimum `0`, maximum `4`, and five-minute scale-down; no endpoint resource appears |
| Evidence posture | Private `platform-evidence` container, blob versioning, 90-day lifecycle, and container-scoped Blob Data Contributor for the workflow principal |
| Secret review | No credential, connection string, signed URI, or sensitive value appeared in the derived JSON; Terraform sensitive markers remain present without values |
| Review result | `rejected_for_apply` |
| Rejection reason | Storage disables shared keys while the Azure ML workspace defaults its system datastore to `AccessKey`; the uploaded artifact also omits the required reviewed JSON representation and its digest |
| Mutation boundary | State lock/read occurred; no Terraform apply or Azure ML workload mutation occurred |

## OIDC-live candidate: 2026-08-12

| Evidence | Sanitized result |
|---|---|
| Platform source commit | `490d60fb9a3fb46f52ba95ce24e944cc45790d10` |
| Reproducible wheel digest | `sha256:f362d7582ef6dae27b3a5c915d2fbebcce13b1554496b6ca60ac7d774e035f5b`; two clean-archive builds matched |
| Generation ID | `sha256:cc099e528c371fb448550f37103b024d8b107203c7878a66a371163e86bb47ea` |
| Manifest digest | `sha256:61e2f5cafe93b65460886ef1189b7df5e9438f8d0c873ebb35f07db96262c588` |
| Resolved-plan digest | `sha256:63f8ddfbdca984274265cf919cf7188726256fb2bfea87b628154465ffbdea81` |
| Template digest | `sha256:c580f27680ab20cbbba5ccfcd7e047c46ac15805b71732b664e4deae6bb87921` |
| Generated-files digest | `sha256:be572abbee2ce0e19cf223b3578254f68fd38d5cce910ae14131aa6155f14be2` |
| Determinism | Byte-identical trees from distinct Python 3.12 `uv` and pip installations; runtime cache files excluded from source-template enumeration |
| Local conformance | 8 tests, Ruff, provenance verification, YAML, actionlint, Terraform init/validate, and scenario scan passed; gitleaks unavailable locally |
| Publication | Product PR `#2` passed required validation and merged to protected `main` as `6532d6605fc497555d26eaeface997e5ac6556d9`; post-merge CI `31621790883` passed |
| OIDC proof | Run `31621923439` passed token identity, Dev-resource-group read, backend-container data read, and expected out-of-scope management denial |
| Mutation boundary | Terraform workload state/write/lock, plan/apply, and Azure ML lifecycle were not exercised |

The first workload-plan attempt, GitHub Actions run `31623045228`, verified generation provenance and completed OIDC login but stopped during `terraform init`. Terraform attempted its Azure CLI user authentication path because the generated workflow did not set the AzureRM OIDC environment contract. No plan or artifact was produced and no workload resource was mutated. Generation `cc099e52...bb47ea` is therefore invalidated for workload planning; the platform template must be corrected and deterministically regenerated before retry.

## Replacement publication candidate: 2026-08-12

| Evidence | Sanitized result |
|---|---|
| Platform source commit | `35356bc` |
| Installed distribution | `enterprise-ml-workflow` `0.1.0` in a clean virtual environment |
| Reproducible wheel digest | `sha256:331e924e069c6ca2b5819076e329bdac85d77684b24dcf8fa4f1b8027e90c837`; two independent clean-archive builds matched |
| Generation ID | `sha256:857b86e6b8566765d3b780549a52100092fc3479d679ac961d5c22c73a835bc6` |
| Manifest digest | `sha256:3f5ebc4abd5e375cbaf2edbb2404427e565b9736226020cff4a45c78ff289cda` |
| Resolved-plan digest | `sha256:d97dc85d30452c4e94aab99194a724286579890d20e98620b6c52eda691bbab3` |
| Template digest | `sha256:8fe6dfb2ef63bfea94fa4bee96b243271b1c6e3e275bf0750ac9ea98f2d98425` |
| Generated-files digest | `sha256:0c3573397127038fdc448b441c66a5169b014522821e0cf3d192704864c838f1` |
| Determinism | Two independent generations from the installed clean wheel were byte-identical |
| Offline doctor | Passed; cloud and OIDC checks correctly reported `not_exercised` |
| Workflow conformance | YAML parse and actionlint passed for CI, plan, apply, training, batch deployment, and OIDC smoke workflows |
| Approval contract | `manual_dispatch_with_plan_digest`; apply consumes the reviewed artifact without replanning; independent human reviewer separation unavailable |
| Publication state | Product commit `915ca008f851645de116993d56cacab0487b6212` pushed to private `main`; initial CI run `31617441559` passed |
| Branch protection | Failed safely with GitHub HTTP `403`: private-repository branch protection requires GitHub Pro or public visibility |
| OIDC consequence | Stopped before dispatch because the `dev` environment admits protected branches and `main` cannot currently be protected |

An earlier wheel built directly from the long-lived worktree was rejected because an ignored stale build artifact entered the wheel. It produced generation `sha256:fbcc524f7a2cd2b108dcc6e87d1dc88d802597a4e2b9bb53adf643c0958dc813`, which is permanently invalidated and was never pushed. Clean archive builds are now the evidence source.

Generation `sha256:e662bc826b5125aaef3563cdc7b73e7e9126d392664aa2cba4964ed38e72116e` is permanently invalidated. GitHub Actions run `31620247861` reached Azure login without issuing an Azure token and proved that this repository emits the immutable subject `repo:rubyrayjuntos@204968804/azure-aiml-ops@1331566719:environment:dev`; the candidate manifest instead declared the conventional repository-name subject. No Terraform workload plan/apply or Azure ML operation occurred.

## Bootstrap deployment: 2026-08-11

The approved bootstrap completed against the remote Entra-authenticated backend. The state container was created privately, imported before planning, and retained throughout. The original saved plan contained 13 creates and one imported-container no-op, with zero changes/deletes and no Owner assignment. GitHub rejected the required-reviewer rule for the private repository because the current billing plan does not support it. Existing resources and state were preserved; a corrective plan containing only the Dev environment and four identifier-only secrets completed successfully.

| Evidence | Sanitized result |
|---|---|
| Original saved-plan digest | `sha256:b65de19ab1dbf79387e8788bcdf879f08dccd9e0fa595e063fba0bc18e4c103a` |
| Corrective saved-plan digest | `sha256:e9931e01c45286c7d44ea13d0f031e91f44ff11c1dacf57fcc7038e9ec23e756` |
| Post-apply plan digest | `sha256:851d7c1037c521f7e89a20716e32f04a3503dc1c71abeedf93d32871361ed0be` |
| Post-apply plan result | Detailed exit code `0`; no changes |
| GitHub repository | Public `rubyrayjuntos/azure-aiml-ops`; generated source is on protected `main` |
| GitHub environment | `dev`; protected-branch rule active; four expected identifier-only secret names verified |
| Manual approval posture | Native reviewers unsupported; digest-bound separate plan/apply fallback implemented locally and pending immutable candidate publication. Independent human reviewer separation is unavailable for the sole operator. |
| Entra application | Single tenant; client ID `72423e94-128f-45f5-a65e-347e9757a2a1` |
| Deployment principal | Service-principal object ID `c5618b4d-3642-483c-83c4-5f7eb37bcb4c` |
| Federated credential | Exact GitHub issuer, ID-qualified `environment:dev` subject, and Azure token-exchange audience verified after identity-only corrective apply |
| Dev resource group | `rg-azure-ai-ml-ops-dev`, East US, provisioning succeeded, approved tags present |
| Backend | Existing account with Shared Key and blob public access disabled; dedicated container private |
| Deployment roles | Container-scoped Blob Data Contributor; Dev-resource-group Contributor and User Access Administrator; no Owner |
| OIDC token exchange | Passed in replacement run `31621923439`; earlier negative run `31620247861` remains immutable diagnostic evidence |
| Azure ML lifecycle | `not_exercised`; bootstrap created no Azure ML workload resources |

## Read-only preflight attempt: 2026-08-11

Execution began at `2026-08-12T01:53:03Z` and stopped before backend, OIDC, RBAC, SKU, or quota queries because required intent was unresolved. This is a blocked preflight attempt, not an authenticated doctor pass or Dev-live evidence.

| Evidence | Sanitized result |
|---|---|
| Candidate generation ID | `sha256:73a2ae86b11cb256cc8680c3a4ff501d0b2982aa9075081f0c2c2497aa39eb6c` |
| Candidate status | `invalidated_before_cloud_preflight` |
| Invalidation reason | Placeholder Azure context and backend references |
| Live resources touched | `false` |
| Generation receipt | Verified before Azure resource queries |
| Platform package | No installed `aiml-scaffold` or `platform-core` distribution was discoverable; candidate was generated from the source worktree |
| Manifest digest | `sha256:c54d79d5b1a4b46410260f6bd83c137c0efd711b5d74cf3049e806c88bf23cff` |
| Resolved-plan digest | `sha256:cf275ccbec2b4ca42b69f64aa85a154ec633bd802cd1555a25a9503f065b3138` |
| Generated-files digest | `sha256:5cd1eb9b0109c8c4a83e677bec6f951b1c1a3b090847649e3d0a4d5a079f49a1` |
| Azure CLI | `2.89.0`; Azure ML extension `2.44.1` |
| Active Azure tenant | `90a7175b-82cd-4815-9050-8cbae3a1d234` |
| Active Azure subscription | `5b452321-32fd-4b1c-8bbf-6d69a5a587ad` |
| Deployment context decision | Tenant and subscription explicitly confirmed for the new clean-room R1 Dev deployment |
| Active identity | User; object ID `a703a773-2881-456b-a8fc-3a007d6c2463` |
| Expected tenant/subscription | Both are zero-value placeholders in the candidate manifest and resolved plan |
| Intended deployment identity | `AZURE_CLIENT_ID` and `AZURE_CLIENT_OBJECT_ID` are unset |
| Backend | Placeholder subscription, resource group, and storage account; not queried |
| Doctor command exit code | Not available: authenticated doctor was deliberately not invoked after stop-condition detection |
| Mutation/deployment checks | Terraform write/lock, plan/apply, OIDC exchange, and Azure ML lifecycle remain `not_exercised` |

Before retrying, discover and approve real backend references, decide the cross-subscription policy, and supply the OIDC subject and intended deployment identity configuration through the release candidate input process. The approved tenant and deployment subscription are `90a7175b-82cd-4815-9050-8cbae3a1d234` and `5b452321-32fd-4b1c-8bbf-6d69a5a587ad`. Installing the immutable platform candidate and regenerating will change the source manifest and therefore creates a replacement candidate whose generation ID must be recorded before evidence collection resumes.

## Read-only discovery: 2026-08-11

Discovery completed at `2026-08-12T01:59:55Z`. It performed management-plane reads, one Entra-authenticated container listing limited to one result, Microsoft Graph application/service-principal reads, and role-assignment reads. It created or changed nothing.

| Discovery item | Sanitized result | Decision state |
|---|---|---|
| Deployment context | Confirmed tenant `90a7175b-82cd-4815-9050-8cbae3a1d234`, subscription `5b452321-32fd-4b1c-8bbf-6d69a5a587ad` | Approved |
| Backend resource group | `rg-azmlops-0001dev-tf` | Approved for shared backend reuse |
| Backend storage account | `stazmlops0001devtf`, East US, shared-key access disabled | Approved for shared backend reuse |
| Existing backend container | Private container `default`; legacy configuration confirms it is the existing Terraform state container | Not reused by R1 |
| R1 backend container | `azure-ai-ml-ops-r1` | Dedicated-container bootstrap planning authorized; not created |
| Backend subscription topology | Same as deployment subscription | `allow_cross_subscription_backend: false` approved |
| Active-user data-plane read | Passed; one blob was observed but its name and contents were not recorded | Discovery evidence only |
| Active inspection identity | User has backend `Storage Blob Data Contributor` and subscription Owner | Must not be used as deployment identity |
| Existing Dev managed identity | `uai-azmlops-0001dev`; no federated credentials and only legacy resource-specific roles | Not suitable as currently configured |
| Existing GitHub application | `gh-azure-mlops-dev-oidc`, client ID `4a03064f-784b-4f7b-a429-46fad02549b5` | Not suitable for R1 |
| Existing GitHub service principal | Object ID `1f783207-33c9-40c5-ab2d-01a1f1510c8e`; application relationship verified | Legacy evidence only |
| Existing federated subjects | Only `rubyrayjuntos/azure-mlops` `main` and `dev` branch subjects | Do not match the new generated repository/environment |
| Existing GitHub principal roles | Includes subscription Owner plus broad Dev/Prod legacy access | Violates R1 least-privilege boundary |
| R1 GitHub identity | No application with an exact new-repository `environment:dev` credential was found | New-identity bootstrap-plan preparation authorized; not created |

### Approved replacement-candidate intent

| Field | Approved value |
|---|---|
| GitHub repository | `rubyrayjuntos/azure-aiml-ops` |
| Product manifest name | `azure-ai-ml-ops` |
| Product display name | `Azure AI ML Ops` |
| Product owner | `Ray Swan` |
| Cost center | `UNASSIGNED` |
| GitHub federated issuer | `https://token.actions.githubusercontent.com` |
| GitHub federated subject | `repo:rubyrayjuntos@204968804/azure-aiml-ops@1331566719:environment:dev` |
| GitHub federated audience | `api://AzureADTokenExchange` |
| Identity posture | New single-tenant application/service principal; no client secret; environment-scoped least privilege |
| Bootstrap authorization | Plan preparation authorized; Azure/Entra execution remains separately approval-gated |
| GitHub repository state | `rubyrayjuntos/azure-aiml-ops` confirmed absent; creation is included in the draft bootstrap plan |

No backend reuse, identity reuse, federated credential change, role assignment, state write/lock, Terraform plan, package build, or candidate regeneration is authorized by this discovery record.

## Bounded replacement correction: 2026-08-12

Generation `f609...d027` and plan run `31623628917` remain immutable with disposition `rejected_before_apply`. Their binary plan and digest are ineligible for reuse.

The replacement platform template now explicitly selects Azure ML identity-based default storage, retains the project workspace's system identity, creates a project-owned compute UAMI for model/MLflow storage operations, and declares purpose-scoped storage data roles and dependency ordering. It also replaces the incomplete two-file review artifact with schema `1.0`'s exact six-file set, structural sanitization, dual digests, provenance/backend/run binding, and action-summary verification. Platform tests and generated-repository static conformance passed locally; the replacement was then published and planned as recorded below. No apply occurred.

### Replacement candidate and saved-plan review

| Evidence | Sanitized result |
|---|---|
| Platform template commit | `08b60bb433c72c0dd57bb46293eb7944f4fa10ed` |
| Platform CI | Run `31625749998` passed |
| Reproducible wheel digest | `sha256:ace2d1b32971d375cfdb061b4afb7229a96634c6d47b49b10a4cc3090a721e01`; two clean builds matched |
| Product generation ID | `sha256:12207f5bb4258460ad549669abd4f1b69f02491bb68f4bc3a3dcb72e6681cdab` |
| Manifest digest | `sha256:61e2f5cafe93b65460886ef1189b7df5e9438f8d0c873ebb35f07db96262c588` |
| Resolved-plan digest | `sha256:63f8ddfbdca984274265cf919cf7188726256fb2bfea87b628154465ffbdea81` |
| Template digest | `sha256:4d3b6d07b9d31a2650c6555d8237f7f0fea1e89ae21e47a9b0a047ec3d77cdca` |
| Generated-files digest | `sha256:76ff382fd870fa4d1628d4e7e374e3030d9a254df7c9da40d14f70697481a978` |
| Product publication | PR `rubyrayjuntos/azure-aiml-ops#4`, merge commit `c399c738bee032b0b2277fd25a6377634d154634`; PR CI `31625919254` and main CI `31626023552` passed |
| Saved-plan run | `31626134587`, attempt `1`; source protected product `main` at `c399c738...4634` |
| Artifact | `terraform-plan-dev-31626134587-1`; six expected files only; expires 2026-09-11 |
| Binary plan digest | `sha256:0441119e4856a086567fe0e228902be4d270a32a617bc7f9e10e1cb40f8ddd44` |
| Sanitized JSON digest | `sha256:428c52cb9effd5e30c991720f23aafcb829a035b297cf94b7b7a2fdce001f468` |
| Independent representation check | Exact Terraform `1.10.0` re-derived byte-identical sanitized JSON from the downloaded binary plan |
| Provider | AzureRM `4.81.0`; lock digest `sha256:e23b20197002dae1c79db71736b06c67c7d4a7fb96b4d1433584c9aa2300c3f4` |
| Action summary | 12 creates; 0 updates; 0 replacements; 0 deletes; 0 reads; 0 no-ops |
| Identity/storage review | Workspace `SystemAssigned`; default storage access `Identity`; Shared Key disabled; project compute UAMI; compute and workflow Storage Blob Data Contributor scopes resolve directly to project storage |
| Principal review | Workflow object ID matches intended deployment principal; compute and workspace principal IDs correctly remain known after apply; post-apply verification is generated and mandatory |
| Boundary review | No bootstrap resource, subscription Owner, ACR, endpoint, Bicep resource, or resource-group overlap; all named workload resources target `rg-azure-ai-ml-ops-dev` |
| Dev posture warnings | Public network access and compute node public IP/local authentication remain enabled for the R1 Dev profile; production private-network conformance is out of scope |
| Apply | Not dispatched and not authorized |

Disposition: `saved_plan_review_passed_apply_not_authorized`.

The reviewed candidate remains immutable evidence, but it is superseded for any future apply by the approved governance-hardening change. The replacement must bind platform source and wheel digests, expiry, Azure context, pre-plan state identity, both reviewed plan digests, allowlisted authorization, and durable apply-result evidence. No apply may use run `31626134587`.

Governance-hardened plan run `31631623498` reached authenticated initialization, captured the empty pre-plan state identity, and created the Terraform plan, then stopped before artifact publication because the generated shell command omitted a continuation before `--state-snapshot`. No apply occurred. The run is retained as negative workflow evidence and its generation is ineligible for apply; the defect must be corrected in the platform template and regenerated.

Current classification:

> **R1 preview—bootstrap-live, OIDC-live, and workload-plan-live conformant; reviewed workload plan saved; apply not authorized; Azure ML Dev lifecycle not live validated.**

## Documentation changelog

| Version | Created | Modified | Who | Notes |
|---|---|---|---|---|
| 1.11.0 | 2026-08-11 | 2026-08-12 | Ray Swan / Codex | Recorded safe negative plan run `31631623498`, the shell-continuation root cause, candidate invalidation, and no-apply boundary. |
| 1.10.0 | 2026-08-11 | 2026-08-12 | Ray Swan / Codex | Preserved saved plan `31626134587` as immutable reviewed evidence but superseded it for apply pending provenance, expiry, state, context, actor, and apply-result hardening. |
| 1.9.0 | 2026-08-11 | 2026-08-12 | Ray Swan / Codex | Recorded replacement generation `12207f5b...1cdab`, protected publication, saved-plan run `31626134587`, six-file artifact digests, independent JSON derivation, successful infrastructure review, and no-apply stop. |
| 1.8.0 | 2026-08-11 | 2026-08-12 | Ray Swan / Codex | Recorded local completion of the bounded AML identity/RBAC and versioned six-file plan-artifact correction; replacement generation and saved plan remain pending. |
| 1.7.0 | 2026-08-11 | 2026-08-12 | Ray Swan / Codex | Recorded saved plan `31623628917`, its immutable digests and ten-create review, and rejection for the Azure ML AccessKey/shared-key contradiction plus incomplete artifact bundle. |
| 1.6.0 | 2026-08-11 | 2026-08-12 | Ray Swan / Codex | Recorded the safe pre-plan initialization failure in run `31623045228` and invalidated generation `cc099e52...bb47ea` for workload planning pending an OIDC environment-contract correction. |
| 1.5.0 | 2026-08-11 | 2026-08-12 | Ray Swan / Codex | Recorded replacement generation `cc099e52...bb47ea`, protected PR publication, passing main CI, and successful nonmutating OIDC proof. |
| 1.4.0 | 2026-08-11 | 2026-08-12 | Ray Swan / Codex | Invalidated generation `e662...2116e`, recorded its safe OIDC subject-mismatch proof, and captured the approved identity-only correction with a clean post-apply plan. |
| 1.3.0 | 2026-08-11 | 2026-08-12 | Ray Swan / Codex | Recorded generated source publication, passing GitHub CI, failed private branch-protection attempt, and deliberate stop before OIDC. |
| 1.2.0 | 2026-08-11 | 2026-08-12 | Ray Swan / Codex | Recorded the reproducible clean wheel, eligible replacement generation and digests, offline validation, and invalidated contaminated local-build candidate. |
| 1.1.0 | 2026-08-11 | 2026-08-12 | Ray Swan / Codex | Corrected the current deployment-identity summary and recorded the locally implemented digest-bound manual approval fallback. |
| 1.0.0 | 2026-08-11 | 2026-08-11 | Ray Swan / Codex | Recorded live bootstrap apply, independent GitHub/Entra/Azure/RBAC verification, clean second plan, and the unsupported GitHub required-reviewer release gate. |
| 0.9.0 | 2026-08-11 | 2026-08-11 | Ray Swan / Codex | Recorded generated Terraform, pinned providers, static validation, protected-environment reviewer constraint, and pending deployment-risk acknowledgement. |
| 0.8.0 | 2026-08-11 | 2026-08-11 | Ray Swan / Codex | Recorded explicit approval of the verified bootstrap plan while retaining separate IaC-generation and execution gates. |
| 0.7.0 | 2026-08-11 | 2026-08-11 | Ray Swan / Codex | Recorded owner and permitted default cost center, GitHub repository absence, and the verified draft bootstrap plan awaiting execution approval. |
| 0.6.0 | 2026-08-11 | 2026-08-11 | Ray Swan / Codex | Recorded approval of same-subscription backend reuse, dedicated R1 container, repository/product identity, exact environment federation subject, and bootstrap-plan preparation. |
| 0.5.0 | 2026-08-11 | 2026-08-11 | Ray Swan / Codex | Recorded same-subscription backend discovery, Entra read success, shared-key posture, and rejection of legacy managed/GitHub identities due to missing federation, wrong subjects, and excessive roles. |
| 0.4.0 | 2026-08-11 | 2026-08-11 | Ray Swan / Codex | Marked generation `73a2...eb6c` invalidated before cloud preflight with no live resources touched and recorded explicit approval of the clean-room Dev tenant/subscription. |
| 0.3.0 | 2026-08-11 | 2026-08-11 | Ray Swan / Codex | Recorded the blocked read-only preflight attempt, active context, verified candidate digests, missing installed package/identity configuration, and deliberate stop before resource queries. |
| 0.2.0 | 2026-08-11 | 2026-08-11 | Ray Swan / Codex | Split authenticated preflight into tenant, subscription, backend, active identity, OIDC configuration/exchange, RBAC, SKU, quota, and receipt-integrity boundaries. |
| 0.1.0 | 2026-08-11 | 2026-08-11 | Ray Swan / Codex | Created the approval-gated R1 Dev clean-room and negative-acceptance evidence matrix. |
