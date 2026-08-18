# ADR 0012: A dedicated Terraform state for shared AI platform infrastructure

## Decision

Azure Databricks and the adopted Foundry/AIServices resource are provisioned from a new, independently-plannable Terraform root, `infra/platform_foundation/`, with its own state — not folded into the existing bootstrap state (`infra/`) and not owned by any generated project's own state.

Backend: the same shared storage account this repository's bootstrap state already uses (`stazmlops0001devtf`), but a new, dedicated state container/key (`aiml-platform-foundation-dev`). R3.2 does not create a new backend storage account — that is a separate, deliberately deferred question (see `docs/architecture/resource-ownership.md`'s R3 inventory).

Naming is intentionally neutral. This is not called a "shared" or "enterprise" platform state, because ownership of what it contains is not yet settled: Databricks is currently classified as factory-owned reference/proving-ground infrastructure (see ADR 0011), and whether the Foundry resource ultimately becomes an enterprise-shared service is an open R4+ question. The state's name should not assert a conclusion the ownership model hasn't reached yet.

This produces three independently-plannable Terraform roots, matching the three lifecycle concepts ADR 0011 and the R3.1 inventory established:

```
infra/                      bootstrap state
  Entra application, GitHub OIDC, environment boundary, prerequisite RBAC

infra/platform_foundation/  platform-foundation state (this ADR)
  Azure Databricks workspace, Databricks Azure-side identity/RBAC,
  adopted Foundry/AIServices account, Foundry deployments, platform-level RBAC

<generated project>/        project state
  AML workspace, project storage, compute, model lifecycle, serving,
  project-specific resources
```

## Rationale

ADR 0001 already establishes that a resource or environment has exactly one IaC owner. `resource-ownership.md` already establishes that centrally owned resources are referenced by immutable Azure resource ID rather than co-managed. This ADR extends the same two principles to a case R1 didn't need to consider: infrastructure that is neither a bootstrap prerequisite nor part of a single generated project, but is still factory-operated.

Folding Databricks/Foundry into the bootstrap state would couple their apply lifecycle to Entra federated-credential and GitHub-OIDC changes — exactly the kind of unintended coupling R3.1 was scoped to remove, not reintroduce. A `terraform -chdir=infra/platform_foundation plan` is guaranteed not to touch GitHub federation, bootstrap identity, or any generated project's infrastructure, simply because those objects are not present in that state - a real blast-radius property, not just an organizational preference.

## Consequences

- R3.2 provisions/imports Databricks and Foundry through `infra/platform_foundation/`, applied independently of `infra/` and of any generated project's own apply.
- The existing Foundry resource (`rg-RSwan-1970`, `Microsoft.CognitiveServices/accounts/rswan-1970-resource`) is imported into this new state rather than recreated. Its current RBAC is a single human grant (`Foundry User` to the operator's own personal login) — no service principal or workload identity has access today. R3.2 must add the deployment/runtime identities this state and its consumers need; it cannot assume any exist.
- Consumers (the churn reference app, and later generated projects) reference these resources by immutable Azure resource ID, the same pattern the environment resource group already uses - never an implicit cross-state dependency.
- The shared backend storage account (`stazmlops0001devtf`) now hosts three distinct state containers/keys, still an explicitly deferred question (not resolved by this ADR) as to whether it should eventually be split.
- Later slices (R3.3 identity proof, R3.4 workload migration, R3.5 Foundry runtime) build on top of this state rather than deciding its boundary as they go.

## Documentation changelog

| Version | Created | Modified | Who | Notes |
|---|---|---|---|---|
| 0.1.0 | 2026-08-18 | 2026-08-18 | Ray Swan / Claude | Initial record of the three-Terraform-root state boundary decision for R3.2. |
