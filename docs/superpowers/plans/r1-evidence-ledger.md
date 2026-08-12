# R1 implementation evidence ledger

This ledger is updated as implementation gates are completed. It must distinguish local/static validation from Dev-live proof.

| Gate | Evidence required | Current status |
|---|---|---|
| Decisions | ADRs for IaC, maturity, evidence, and topology | Implemented locally |
| Contract kernel | Manifest, provider catalog, policy, explicit Azure context, plan, typed extensions, CLI errors, provenance, and negative-combination tests | Passed locally: platform suite includes 101 tests |
| Evidence kernel | Versioned identity, URI conformance, idempotency, redaction, composite receipts, and invalid-timeline projection | Passed locally, including signed URI, sequence, transition, terminal ID/state/artifact/payload, context, identity-content, duplicate/conflicting receipt, cross-project, and ordering tests |
| Generator | Two byte-identical outputs and deterministic receipt | Passed from two clean wheel builds and distinct Python 3.12 installation paths; runtime cache files are excluded from template enumeration and hashing |
| Generated provenance | Source manifest, resolved plan, constraints, templates, and generated tree | Independently digest-verified by offline doctor |
| Generated repository | Tests, Ruff, YAML, Terraform, workflow lint, dependency resolution, and secret scan | Passed locally: digest-bound plan/apply and OIDC workflows included; Ruff, YAML parse, actionlint, Terraform 4.81.0 init/validate, Python dependency and targeted secret/scenario checks passed |
| Doctor hardening | Context, active/intended identity, backend management/data planes, shared-key posture, OIDC configuration, scoped RBAC, SKU/quota, and unexercised boundaries | Passed with mocked read-only Azure responses and negative paths; offline generated-project doctor passed |
| Authenticated doctor | Real tenant/subscription context, resource group, backend, quotas, OIDC configuration, and RBAC | Bootstrap context, backend, OIDC configuration, and RBAC are live; GitHub OIDC proof run `31621923439` passed against replacement generation `cc099e52...bb47ea` |
| Azure ML service schema | Pipeline compute/reference validation in a real workspace | Not executed; `az ml job validate` requires the not-yet-approved clean-room workspace |
| Dev clean-room | Terraform apply, Azure ML run, registration, batch invocation, evidence, second clean plan | Bootstrap-only Terraform apply and clean second plan passed; generated Azure ML workload remains unprovisioned and unexecuted |
| R1 release | Immutable package/template/workflow versions and compatibility matrix | Platform branch and replacement candidate published through protected PR; generated CI and read-only OIDC proof passed; Azure ML workload planning remains approval-gated |

## Candidate lineage

| Generation ID | Status | Reason | Live resources touched |
|---|---|---|---|
| `sha256:73a2ae86b11cb256cc8680c3a4ff501d0b2982aa9075081f0c2c2497aa39eb6c` | `invalidated_before_cloud_preflight` | Placeholder Azure context and backend references | `false` |
| `sha256:fbcc524f7a2cd2b108dcc6e87d1dc88d802597a4e2b9bb53adf643c0958dc813` | `invalidated_before_publication` | Built from a dirty local build directory that contributed a stale deleted template; never pushed | `false` |
| `sha256:857b86e6b8566765d3b780549a52100092fc3479d679ac961d5c22c73a835bc6` | `published_oidc_blocked` | Product commit `915ca008f851645de116993d56cacab0487b6212` passed CI; private-repository branch protection requires GitHub Pro or public visibility | GitHub source only; no Azure workload |
| `sha256:e662bc826b5125aaef3563cdc7b73e7e9126d392664aa2cba4964ed38e72116e` | `invalidated_after_negative_oidc_proof` | Run `31620247861` proved GitHub emits the ID-qualified subject; Azure login failed before token issuance | GitHub workflow only; no Azure workload |
| `sha256:cc099e528c371fb448550f37103b024d8b107203c7878a66a371163e86bb47ea` | `oidc_read_only_proven_plan_invalidated` | OIDC proof `31621923439` passed; plan run `31623045228` then stopped at init because the workflow omitted AzureRM's OIDC environment contract | OIDC token plus authorized/denied reads only; no plan artifact or Azure ML workload mutation |

This entry is immutable history and must not be overwritten by the replacement candidate. Read-only discovery subsequently confirmed the intended tenant/subscription and found a same-subscription backend candidate, but no suitable least-privilege R1 GitHub OIDC identity.

For historical traceability, generation `857b...35bc6` used wheel digest `sha256:331e924e069c6ca2b5819076e329bdac85d77684b24dcf8fa4f1b8027e90c837` from commit `35356bc`. Its manifest, resolved-plan, template, and generated-files digests were respectively `sha256:3f5ebc4abd5e375cbaf2edbb2404427e565b9736226020cff4a45c78ff289cda`, `sha256:d97dc85d30452c4e94aab99194a724286579890d20e98620b6c52eda691bbab3`, `sha256:8fe6dfb2ef63bfea94fa4bee96b243271b1c6e3e275bf0750ac9ea98f2d98425`, and `sha256:0c3573397127038fdc448b441c66a5169b014522821e0cf3d192704864c838f1`. It is not the current candidate.

## Documentation changelog

| Version | Created | Modified | Who | Notes |
|---|---|---|---|---|
| 1.1.0 | 2026-08-11 | 2026-08-12 | Ray Swan / Codex | Recorded safe workload-plan initialization failure `31623045228` and the generated AzureRM OIDC environment-contract correction. |
| 1.0.0 | 2026-08-11 | 2026-08-12 | Ray Swan / Codex | Recorded deterministic cross-installer regeneration, protected publication of generation `cc099e52...bb47ea`, and successful nonmutating GitHub OIDC proof. |
| 0.9.0 | 2026-08-11 | 2026-08-12 | Ray Swan / Codex | Recorded platform PR, generated product commit, successful CI, and the GitHub-plan branch-protection blocker that stopped OIDC execution. |
| 0.8.0 | 2026-08-11 | 2026-08-12 | Ray Swan / Codex | Recorded immutable platform commit, reproducible clean wheel, invalidated dirty-build candidate, and eligible replacement generation. |
| 0.7.0 | 2026-08-11 | 2026-08-12 | Ray Swan / Codex | Recorded the 100-test suite and locally conformant digest-bound approval and OIDC workflow contracts before candidate publication. |
| 0.6.0 | 2026-08-11 | 2026-08-11 | Ray Swan / Codex | Recorded live bootstrap prerequisites and clean Terraform convergence while retaining the replacement-candidate doctor and Azure ML lifecycle boundaries. |
| 0.5.0 | 2026-08-11 | 2026-08-11 | Ray Swan / Codex | Retained the invalidated generation in candidate lineage and recorded the negative preflight and read-only backend/OIDC discovery boundary. |
| 0.4.0 | 2026-08-11 | 2026-08-11 | Ray Swan / Codex | Recorded explicit Azure context, composite receipt/projector integrity, tri-state doctor tests, 98-test platform suite, and the still-pending authenticated boundary. |
| 0.3.0 | 2026-08-11 | 2026-08-11 | Ray Swan / Codex | Recorded R1 preflight hardening, provenance, dependency resolution, and final local conformance. |
| 0.2.0 | 2026-08-11 | 2026-08-11 | Ray Swan / Codex | Recorded completed local/static gates and the authenticated and live Azure boundaries. |
| 0.1.0 | 2026-08-11 | 2026-08-11 | Ray Swan / Codex | Created the local, static, and live R1 evidence ledger. |
