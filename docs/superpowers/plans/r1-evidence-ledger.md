# R1 implementation evidence ledger

This ledger is updated as implementation gates are completed. It must distinguish local/static validation from Dev-live proof.

| Gate | Evidence required | Current status |
|---|---|---|
| Decisions | ADRs for IaC, maturity, evidence, and topology | Implemented locally |
| Contract kernel | Manifest, provider catalog, policy, explicit Azure context, plan, typed extensions, CLI errors, provenance, and negative-combination tests | Passed locally: platform suite included 100 tests |
| Evidence kernel | Versioned identity, URI conformance, idempotency, redaction, composite receipts, and invalid-timeline projection | Passed locally, including signed URI, sequence, transition, terminal ID/state/artifact/payload, context, identity-content, duplicate/conflicting receipt, cross-project, and ordering tests |
| Generator | Two byte-identical outputs and deterministic receipt | Passed locally; first preflight candidate retained below as invalidated |
| Generated provenance | Source manifest, resolved plan, constraints, templates, and generated tree | Independently digest-verified by offline doctor |
| Generated repository | Tests, Ruff, YAML, Terraform, workflow lint, dependency resolution, and secret scan | Passed locally: digest-bound plan/apply and OIDC workflows included; Ruff, YAML parse, actionlint, Terraform 4.81.0 init/validate, Python dependency and targeted secret/scenario checks passed |
| Doctor hardening | Context, active/intended identity, backend management/data planes, shared-key posture, OIDC configuration, scoped RBAC, SKU/quota, and unexercised boundaries | Passed with mocked read-only Azure responses and negative paths; offline generated-project doctor passed |
| Authenticated doctor | Real tenant/subscription context, resource group, backend, quotas, OIDC configuration, and RBAC | Bootstrap context, backend, OIDC configuration, and RBAC are now live and independently verified; full candidate-bound doctor still awaits immutable package and replacement generation |
| Azure ML service schema | Pipeline compute/reference validation in a real workspace | Not executed; `az ml job validate` requires the not-yet-approved clean-room workspace |
| Dev clean-room | Terraform apply, Azure ML run, registration, batch invocation, evidence, second clean plan | Bootstrap-only Terraform apply and clean second plan passed; generated Azure ML workload remains ungenerated and unexecuted |
| R1 release | Immutable package/template/workflow versions and compatibility matrix | Candidate publication authorized; digest-bound approval implementation passes locally but is not yet committed or published |

## Candidate lineage

| Generation ID | Status | Reason | Live resources touched |
|---|---|---|---|
| `sha256:73a2ae86b11cb256cc8680c3a4ff501d0b2982aa9075081f0c2c2497aa39eb6c` | `invalidated_before_cloud_preflight` | Placeholder Azure context and backend references | `false` |

This entry is immutable history and must not be overwritten by the replacement candidate. Read-only discovery subsequently confirmed the intended tenant/subscription and found a same-subscription backend candidate, but no suitable least-privilege R1 GitHub OIDC identity.

## Documentation changelog

| Version | Created | Modified | Who | Notes |
|---|---|---|---|---|
| 0.7.0 | 2026-08-11 | 2026-08-12 | Ray Swan / Codex | Recorded the 100-test suite and locally conformant digest-bound approval and OIDC workflow contracts before candidate publication. |
| 0.6.0 | 2026-08-11 | 2026-08-11 | Ray Swan / Codex | Recorded live bootstrap prerequisites and clean Terraform convergence while retaining the replacement-candidate doctor and Azure ML lifecycle boundaries. |
| 0.5.0 | 2026-08-11 | 2026-08-11 | Ray Swan / Codex | Retained the invalidated generation in candidate lineage and recorded the negative preflight and read-only backend/OIDC discovery boundary. |
| 0.4.0 | 2026-08-11 | 2026-08-11 | Ray Swan / Codex | Recorded explicit Azure context, composite receipt/projector integrity, tri-state doctor tests, 98-test platform suite, and the still-pending authenticated boundary. |
| 0.3.0 | 2026-08-11 | 2026-08-11 | Ray Swan / Codex | Recorded R1 preflight hardening, provenance, dependency resolution, and final local conformance. |
| 0.2.0 | 2026-08-11 | 2026-08-11 | Ray Swan / Codex | Recorded completed local/static gates and the authenticated and live Azure boundaries. |
| 0.1.0 | 2026-08-11 | 2026-08-11 | Ray Swan / Codex | Created the local, static, and live R1 evidence ledger. |
