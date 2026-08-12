# R1 Dev clean-room evidence matrix

This matrix must be completed with independently verifiable Dev evidence. Creating the matrix does not authorize authenticated checks, Terraform operations, Azure ML jobs, endpoint changes, or resource destruction.

## Pre-apply

| Gate | Required evidence | Status |
|---|---|---|
| Explicit Azure context | Expected tenant and deployment subscription match the active CLI context | Confirmed for replacement candidate; invalidated candidate still contains placeholders |
| Real bootstrap references | Backend resource group, storage account, container, backend subscription, and cross-subscription policy result | Live: same-subscription backend and dedicated private `azure-ai-ml-ops-r1` container verified |
| Backend management plane | Storage account and state container are independently visible | Live: account and dedicated container independently verified |
| Backend data plane | Active CLI identity can list state blobs using Entra authentication; write and lock remain unexercised | Live bootstrap state write and lock exercised through Terraform; deployment-principal OIDC exchange remains unexercised |
| Environment-scoped OIDC | Application/client ID, principal/object ID, federated credential, exact environment roles, and no subscription Owner | Live: app/principal relationship, exact issuer/subject/audience, three scoped roles, and absence of Owner verified |
| OIDC token exchange | Actual GitHub workflow exchanges a token as the intended deployment identity | Not exercised by local doctor |
| Authenticated doctor | Separate context, identity, backend, shared-key, OIDC configuration, RBAC, SKU, and quota results | Earlier candidate stopped before resource queries; bootstrap configuration is live, but replacement-candidate doctor remains pending |
| Active identity boundary | Local CLI identity is recorded separately from the intended GitHub deployment identity | Deployment identity is configured and exact federation verified; actual GitHub token exchange remains unexercised |
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

## Bootstrap deployment: 2026-08-11

The approved bootstrap completed against the remote Entra-authenticated backend. The state container was created privately, imported before planning, and retained throughout. The original saved plan contained 13 creates and one imported-container no-op, with zero changes/deletes and no Owner assignment. GitHub rejected the required-reviewer rule for the private repository because the current billing plan does not support it. Existing resources and state were preserved; a corrective plan containing only the Dev environment and four identifier-only secrets completed successfully.

| Evidence | Sanitized result |
|---|---|
| Original saved-plan digest | `sha256:b65de19ab1dbf79387e8788bcdf879f08dccd9e0fa595e063fba0bc18e4c103a` |
| Corrective saved-plan digest | `sha256:e9931e01c45286c7d44ea13d0f031e91f44ff11c1dacf57fcc7038e9ec23e756` |
| Post-apply plan digest | `sha256:851d7c1037c521f7e89a20716e32f04a3503dc1c71abeedf93d32871361ed0be` |
| Post-apply plan result | Detailed exit code `0`; no changes |
| GitHub repository | Private `rubyrayjuntos/azure-aiml-ops`; intentionally empty pending separate source-push authorization; no default/protected branch exists yet |
| GitHub environment | `dev`; protected-branch rule active; four expected identifier-only secret names verified |
| Manual approval posture | Native reviewers unsupported; digest-bound separate plan/apply fallback implemented locally and pending immutable candidate publication. Independent human reviewer separation is unavailable for the sole operator. |
| Entra application | Single tenant; client ID `72423e94-128f-45f5-a65e-347e9757a2a1` |
| Deployment principal | Service-principal object ID `c5618b4d-3642-483c-83c4-5f7eb37bcb4c` |
| Federated credential | Exact GitHub issuer, `environment:dev` subject, and Azure token-exchange audience verified |
| Dev resource group | `rg-azure-ai-ml-ops-dev`, East US, provisioning succeeded, approved tags present |
| Backend | Existing account with Shared Key and blob public access disabled; dedicated container private |
| Deployment roles | Container-scoped Blob Data Contributor; Dev-resource-group Contributor and User Access Administrator; no Owner |
| OIDC token exchange | `not_exercised`; requires an actual GitHub Actions run |
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
| GitHub federated subject | `repo:rubyrayjuntos/azure-aiml-ops:environment:dev` |
| GitHub federated audience | `api://AzureADTokenExchange` |
| Identity posture | New single-tenant application/service principal; no client secret; environment-scoped least privilege |
| Bootstrap authorization | Plan preparation authorized; Azure/Entra execution remains separately approval-gated |
| GitHub repository state | `rubyrayjuntos/azure-aiml-ops` confirmed absent; creation is included in the draft bootstrap plan |

No backend reuse, identity reuse, federated credential change, role assignment, state write/lock, Terraform plan, package build, or candidate regeneration is authorized by this discovery record.

## Documentation changelog

| Version | Created | Modified | Who | Notes |
|---|---|---|---|---|
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
