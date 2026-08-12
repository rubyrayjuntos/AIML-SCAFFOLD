# R1 compatibility matrix

This matrix records what AIML-SCAFFOLD R1 can resolve and generate. It does not claim live deployment evidence.

| Contract | R1 selection | Maturity before clean-room proof | Generated | Notes |
|---|---|---:|---:|---|
| Manifest schema | `1.0` | stable | yes | Unsupported versions fail validation. |
| Platform | `1.0.0` | stable | yes | Written into plans and receipts. |
| Azure context | Explicit tenant, deployment subscription, backend subscription, and identity references | preview | yes | Cross-subscription state requires explicit policy. |
| Azure IaC | Terraform | preview | yes | Sole R1 generated IaC provider. |
| Training/evaluation | Azure ML | preview | yes | Job and evaluation contracts included. |
| Registry | Azure ML | preview | yes | Conditional registration only. |
| Serving | Azure ML batch | preview | yes | Explicit registered model version required. |
| Evidence | Azure Blob | preview | yes | Project-local events and receipts use composite project/environment/operation identity. |
| Evidence identity | `1.0` | preview | yes | Canonical eight-field identity with visible integrity failures. |
| Provenance | Manifest, plan, constraints, receipt | preview | yes | Semantic and byte-level digests are verified. |
| Deployment approval | `manual_dispatch_with_plan_digest` | preview | yes | Separate dispatch verifies and applies the reviewed binary plan without replanning; no independent-reviewer claim for a sole operator. |
| Bicep | experimental reference | experimental | no | Must not target Terraform-owned environments. |
| Online serving | Azure ML | preview | no | Deferred to R1.1. |
| Monitoring/retraining | Azure ML | experimental | no | Deferred to R1.2. |
| Foundry/Search | planned | planned | no | Deferred to R2. |
| Hybrid tools | planned | planned | no | Deferred to R3. |
| Databricks | planned | planned | no | Deferred to R4. |

Preview R1 providers require both manifest permission and `--allow-experimental`. Planned capabilities are rejected regardless of override. Providers may move to stable only after recorded clean-room evidence meets the R1 GA gate.

## Documentation changelog

| Version | Created | Modified | Who | Notes |
|---|---|---|---|---|
| 1.0.0-rc4 | 2026-08-11 | 2026-08-12 | Ray Swan / Codex | Added digest-bound manual approval and read-only GitHub OIDC proof contracts. |
| 1.0.0-rc3 | 2026-08-11 | 2026-08-11 | Ray Swan / Codex | Added explicit Azure context/cross-subscription policy and composite evidence receipt contracts. |
| 1.0.0-rc2 | 2026-08-11 | 2026-08-11 | Ray Swan / Codex | Added versioned evidence identity and generated provenance compatibility contracts. |
| 1.0.0-rc1 | 2026-08-11 | 2026-08-11 | Ray Swan / Codex | Initial R1 platform, provider, maturity, and release compatibility matrix. |
