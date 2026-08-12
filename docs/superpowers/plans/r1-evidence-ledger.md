# R1 implementation evidence ledger

This ledger is updated as implementation gates are completed. It must distinguish local/static validation from Dev-live proof.

| Gate | Evidence required | Current status |
|---|---|---|
| Decisions | ADRs for IaC, maturity, evidence, and topology | Implemented locally |
| Contract kernel | Manifest, provider catalog, policy, explicit Azure context, plan, typed extensions, CLI errors, provenance, and negative-combination tests | Passed locally: platform suite included 100 tests |
| Evidence kernel | Versioned identity, URI conformance, idempotency, redaction, composite receipts, and invalid-timeline projection | Passed locally, including signed URI, sequence, transition, terminal ID/state/artifact/payload, context, identity-content, duplicate/conflicting receipt, cross-project, and ordering tests |
| Generator | Two byte-identical outputs and deterministic receipt | Passed from the clean installed wheel; replacement candidate recorded below |
| Generated provenance | Source manifest, resolved plan, constraints, templates, and generated tree | Independently digest-verified by offline doctor |
| Generated repository | Tests, Ruff, YAML, Terraform, workflow lint, dependency resolution, and secret scan | Passed locally: digest-bound plan/apply and OIDC workflows included; Ruff, YAML parse, actionlint, Terraform 4.81.0 init/validate, Python dependency and targeted secret/scenario checks passed |
| Doctor hardening | Context, active/intended identity, backend management/data planes, shared-key posture, OIDC configuration, scoped RBAC, SKU/quota, and unexercised boundaries | Passed with mocked read-only Azure responses and negative paths; offline generated-project doctor passed |
| Authenticated doctor | Real tenant/subscription context, resource group, backend, quotas, OIDC configuration, and RBAC | Bootstrap context, backend, OIDC configuration, and RBAC are live; replacement candidate passed offline doctor and awaits GitHub OIDC proof |
| Azure ML service schema | Pipeline compute/reference validation in a real workspace | Not executed; `az ml job validate` requires the not-yet-approved clean-room workspace |
| Dev clean-room | Terraform apply, Azure ML run, registration, batch invocation, evidence, second clean plan | Bootstrap-only Terraform apply and clean second plan passed; generated Azure ML workload remains ungenerated and unexecuted |
| R1 release | Immutable package/template/workflow versions and compatibility matrix | Platform branch and generated candidate published; generated CI passed; OIDC proof blocked by unavailable private-repository branch protection |

## Candidate lineage

| Generation ID | Status | Reason | Live resources touched |
|---|---|---|---|
| `sha256:73a2ae86b11cb256cc8680c3a4ff501d0b2982aa9075081f0c2c2497aa39eb6c` | `invalidated_before_cloud_preflight` | Placeholder Azure context and backend references | `false` |
| `sha256:fbcc524f7a2cd2b108dcc6e87d1dc88d802597a4e2b9bb53adf643c0958dc813` | `invalidated_before_publication` | Built from a dirty local build directory that contributed a stale deleted template; never pushed | `false` |
| `sha256:857b86e6b8566765d3b780549a52100092fc3479d679ac961d5c22c73a835bc6` | `published_oidc_blocked` | Product commit `915ca008f851645de116993d56cacab0487b6212` passed CI; private-repository branch protection requires GitHub Pro or public visibility | GitHub source only; no Azure workload |

This entry is immutable history and must not be overwritten by the replacement candidate. Read-only discovery subsequently confirmed the intended tenant/subscription and found a same-subscription backend candidate, but no suitable least-privilege R1 GitHub OIDC identity.

The eligible wheel is `enterprise_ml_workflow-0.1.0-py3-none-any.whl` with digest `sha256:331e924e069c6ca2b5819076e329bdac85d77684b24dcf8fa4f1b8027e90c837`. Two builds from independent clean `git archive` exports of commit `35356bc` with the same source epoch were byte-identical. The replacement candidate's manifest, resolved-plan, template, and generated-files digests are respectively `sha256:3f5ebc4abd5e375cbaf2edbb2404427e565b9736226020cff4a45c78ff289cda`, `sha256:d97dc85d30452c4e94aab99194a724286579890d20e98620b6c52eda691bbab3`, `sha256:8fe6dfb2ef63bfea94fa4bee96b243271b1c6e3e275bf0750ac9ea98f2d98425`, and `sha256:0c3573397127038fdc448b441c66a5169b014522821e0cf3d192704864c838f1`.

## Documentation changelog

| Version | Created | Modified | Who | Notes |
|---|---|---|---|---|
| 0.9.0 | 2026-08-11 | 2026-08-12 | Ray Swan / Codex | Recorded platform PR, generated product commit, successful CI, and the GitHub-plan branch-protection blocker that stopped OIDC execution. |
| 0.8.0 | 2026-08-11 | 2026-08-12 | Ray Swan / Codex | Recorded immutable platform commit, reproducible clean wheel, invalidated dirty-build candidate, and eligible replacement generation. |
| 0.7.0 | 2026-08-11 | 2026-08-12 | Ray Swan / Codex | Recorded the 100-test suite and locally conformant digest-bound approval and OIDC workflow contracts before candidate publication. |
| 0.6.0 | 2026-08-11 | 2026-08-11 | Ray Swan / Codex | Recorded live bootstrap prerequisites and clean Terraform convergence while retaining the replacement-candidate doctor and Azure ML lifecycle boundaries. |
| 0.5.0 | 2026-08-11 | 2026-08-11 | Ray Swan / Codex | Retained the invalidated generation in candidate lineage and recorded the negative preflight and read-only backend/OIDC discovery boundary. |
| 0.4.0 | 2026-08-11 | 2026-08-11 | Ray Swan / Codex | Recorded explicit Azure context, composite receipt/projector integrity, tri-state doctor tests, 98-test platform suite, and the still-pending authenticated boundary. |
| 0.3.0 | 2026-08-11 | 2026-08-11 | Ray Swan / Codex | Recorded R1 preflight hardening, provenance, dependency resolution, and final local conformance. |
| 0.2.0 | 2026-08-11 | 2026-08-11 | Ray Swan / Codex | Recorded completed local/static gates and the authenticated and live Azure boundaries. |
| 0.1.0 | 2026-08-11 | 2026-08-11 | Ray Swan / Codex | Created the local, static, and live R1 evidence ledger. |
