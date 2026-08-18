# ADR 0014: Factory and generated-project workflows use separate Azure identities

## Decision

Factory-floor GitHub Actions workflows (this repository, `AIML-SCAFFOLD`) and generated-project GitHub Actions workflows (e.g. `azure-aiml-ops`) authenticate to Azure through **separate Entra applications/service principals**, each with its own federated credential(s) and its own, narrower RBAC grants. Neither identity is a superset or reused copy of the other.

Concretely: `gh-azure-ai-ml-ops-r1-dev-oidc` (R1's original deployment identity) retains only the RBAC a generated project's own Terraform needs. A new identity, `gh-aiml-scaffold-platform-oidc`, is created for the factory's own `infra/` and `infra/platform_foundation/` applies, holding only the RBAC those roots need.

## Rationale

Discovered while building R3.2 Step F: adding a second federated credential to the *existing* `gh-azure-ai-ml-ops-r1-dev-oidc` application — one scoped to `AIML-SCAFFOLD`'s environment, alongside the existing one scoped to `azure-aiml-ops`'s environment — would have let a workflow running in either repository exchange a token for the **same underlying service principal**. Federated credentials isolate *token issuance context* (which repo/environment can request a token), not the RBAC permissions of the principal that token represents. Any Azure role granted to that principal for factory purposes would silently become available to the generated project's workflow too, and vice versa.

This was not hypothetical: by the time this was caught, R3.2 Steps A and D had already granted platform-foundation-management RBAC (`Storage Blob Data Contributor` on the new state container, `Contributor` on the Databricks resource group, `Cognitive Services Contributor` on the Foundry account) to the shared identity — meaning `azure-aiml-ops`'s existing, already-federated OIDC credential could have exercised those grants immediately, without R3.2's own workflows ever running. See the R3.2 plan's execution log for the correction (RBAC moved to the new factory identity).

## The rule

> Factory workflows and generated-project workflows must not share an Azure authorization principal when their required resource scopes differ. Federated credentials isolate token issuance context, not the RBAC permissions of the underlying service principal.

This generalizes ADR 0011's no-accidental-inheritance invariant from *resources* to *identities*: a generated project must not inherit factory-owned resource access, and a generated project's deployment identity must not inherit factory-scoped RBAC either, even transitively through a shared principal. A generated car does not get the keys to the factory merely because they came off the same assembly line.

## Consequences

- Every future Entra application created for CI/CD purposes must be scoped to exactly one deployment context (one repository, one class of resources it manages) - reusing an application across factory and generated-project contexts is prohibited by default, not just discouraged.
- `infra/` (bootstrap) now provisions two Entra applications instead of one: the existing R1/generated-project identity, and the new factory identity. Both remain bootstrap-owned per ADR 0001.
- R3.2's Step A and Step D RBAC grants, originally applied to the shared identity, were moved to the new factory identity as part of this correction - not left in place as a "temporary" exception.
- Any later R-slice adding a new CI/CD workflow must ask which identity category (factory vs. generated-project vs. a new category) it belongs to before reusing an existing application, rather than defaulting to whatever identity happens to already have working secrets configured.

## Documentation changelog

| Version | Created | Modified | Who | Notes |
|---|---|---|---|---|
| 0.1.0 | 2026-08-18 | 2026-08-18 | Ray Swan / Claude | Initial record of the factory/generated-project identity separation rule, discovered and corrected during R3.2 Step F. |
