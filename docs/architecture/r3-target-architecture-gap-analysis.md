# R3 target architecture: As-Is, To-Be, and gap analysis

R3 is governed as an enterprise migration from a known As-Is implementation to an explicit To-Be architecture. The purpose of this document is to distinguish already-proven capability from remaining migration, ownership, identity, configuration, and integration gaps so later slices do not re-test solved problems.

This document exists because R3's early slices drifted into re-verifying capabilities (Databricks retrieval, Foundry model calls, agent/LLM orchestration) that were already proven — first in the user's original standalone `cust-churn` prototype, then again in this repo's R3 Slice 1 retrieval work. The open question was never "does this technology work?" It is: **can the factory reproduce the same working system inside the target enterprise architecture** — correct resource ownership, correct Terraform state boundaries, correct identities, least privilege, no accidental inheritance, no cross-tenant credential borrowing, reproducible GitHub-governed deployment — **without carrying forward any of the informal assumptions that made the prototype easy to build?**

## As-Is architecture

A working, already-proven system exists, built across three prior efforts:

- **`cust-churn` v1 and `azuredev-3d78/cust-churn` v2** — standalone prototypes, outside this repo, that proved the full chain end-to-end: Databricks retrieval/data → Foundry → AI application → a working churn assistant.
- **This repo's R1/R2** — proved the ML control plane, training foundation, and model lifecycle closure (deploy → infer → observe → detect → retrain → compare → promote, bounded by two external Azure platform defects).
- **This repo's R3 Slice 1** — proved real vector retrieval (notes/tickets/playbooks indexes) against live Databricks data, but on a separate, cross-tenant workspace (the old `n2arts2000`/Yahoo tenant), and deliberately did not touch the Foundry/LLM call site.

The capability is proven. The architecture it was proven on is not the target architecture: cross-tenant Databricks dependency, a Foundry resource adopted informally, and a generated project's own compute identity carrying a live RBAC grant onto a factory-owned resource.

## To-Be architecture

The target is a "starter store" shape, matching this project's Salesforce-implementation-partner framing (ADR 0011): a generated project must be able to leave the factory and operate independently.

```
                     ENTERPRISE AZURE
                           |
             +-------------+-------------+
             |                           |
      shared platform services     enterprise governance
      (when explicitly selected)   (tenant / policies / etc.)
             |
             | resource IDs + contracts
             v
                  GENERATED PROJECT
                  =================
project repo
|
+-- project manifest/config
|
+-- application
+-- ML lifecycle
+-- agents
+-- retrieval
+-- evaluation
+-- monitoring
+-- Terraform
+-- GitHub Actions
             |
             v
project-specific Azure resources
|
+-- AML / compute
+-- storage
+-- project identities
+-- model registry
+-- serving
+-- project-specific infrastructure
             |
             | explicit consumption only
             v
optional platform capabilities
+-- Databricks
+-- Foundry
+-- enterprise monitoring
+-- shared semantic layer
+-- other approved services
```

The critical property: a generated project does not know about the factory repository, does not depend on the factory's credentials, does not inherit factory identities, does not read factory Terraform state. Anything it consumes from outside its own boundary — Databricks, Foundry, shared monitoring — arrives as an explicit resource/configuration contract, never an inherited permission.

## Gap analysis

| Domain | As-Is | To-Be | Gap | Status |
|---|---|---|---|---|
| Databricks | Slice 1 proved retrieval on a separate/cross-tenant workspace | Primary-subscription governed workspace (`dbw-aiml-platform-foundation-dev`, provisioned R3.2) | Migrate Delta tables/vector indexes + move workload auth off `databricks auth login` OAuth profile onto workload identity | R3.4 |
| Foundry | Working resource, manually established (`rg-RSwan-1970`); Terraform-adopted in R3.2 | Explicit consumer contract via a dedicated reference-runtime identity | RBAC grant currently held by the generated project's own compute identity — wrong owner | **R3.3, in progress** |
| Runtime identity | Generated-project AML compute identity (`id-azure-ai-ml-ops-dev-compute`) holds a live Foundry grant | Three-identity model: factory-deploy / factory-reference-runtime / generated-project | Create a new factory/reference-runtime identity, move the grant, add a negative-control test proving the generated-project identity is denied | **R3.3, in progress** |
| GitHub deploy identity | — | Separate factory identity, isolated from the generated project's OIDC credential (ADR 0014) | — | **Closed, R3.2** |
| Terraform state | Multiple historical boundaries (shared backend account with the legacy `azmlops` project) | Explicit bootstrap / `platform_foundation` / project state separation (ADR 0012) | Prod per-environment parameterization deliberately deferred and documented, not a live gap | Mostly closed |
| Retrieval | Proven (Slice 1, old cross-tenant workspace) | Same capability, live on the target workspace | **Migration validation, not capability discovery** — the capability itself is not being rediscovered, but R3.4 still has to prove the migrated path on the target workspace and identity | R3.4 |
| Agent/LLM runtime | Proven in the original `cust-churn` prototype; **not proven in this repo** — `/api/v1/assistant` still unconditionally returns `response_source="deterministic_fallback"`, no retrieval or Foundry call exists in this codebase's call site | Config-driven, governed, wired to a real endpoint, citations enforced | First real wiring of retrieval → Foundry → `/api/v1/assistant` in this repo, through declared contracts | R3.5 |
| Permissions | **Mixed: some deliberate platform RBAC from R3.2, plus legacy/generated-project identity reuse** | Least privilege by ownership/lifecycle, proven with positive and negative tests | **R3.3's core deliverable** | In progress |
| Configuration | Scenario-specific wiring (`scenario.yaml`/`config.yaml`/`Settings`) | Manifest/config-driven project variation — the code → configuration → business-accessible-configuration progression (ADR 0011) | Ongoing through R3.5/R4, not closed by this document | Deferred |
| Observability | Partial, service-specific | Cross-service OTel + SLO contract | Explicitly R5, not R3 (see `dais-2026-r4-r5-implications` session memory) | Filed |
| Recovery | Manual, governed decisions | Automated bounded recovery (promotion gates, rollback, drift-triggered remediation) | Explicitly R6, not R3 | Filed |

## Reframed R3 slices

The slice numbers stay as planning/commit increments; their acceptance criteria are corrected to stop re-testing already-proven capability.

- **R3.3 — Identity & authorization architecture.** Not "can Foundry work?" — already known. Proves: the factory-deploy identity can administer factory resources; the new factory/reference-runtime identity can consume permitted platform services (Foundry, Databricks); the generated-project identity *cannot* reach factory-owned resources (negative-control proof); an unapproved identity is denied. Scoped to small, non-mutating live smoke proofs — parallel to R3.2 Step G's OIDC smoke test — not a re-run of churn business logic.
- **R3.4 — Reference implementation migration.** Not "does retrieval work?" — already proven. Migrates the known-working churn retrieval workload (Delta tables, vector indexes, queries) onto the target Databricks workspace, using the R3.3 reference-runtime identity. Migration validation, not capability discovery.
- **R3.5 — Governed assistant integration + independent project contract proof.** Wires `retrieval → Foundry → /api/v1/assistant` through declared config/identity contracts, for the first time in this repo, with the existing `require_citations: true` contract (`foundry/agents/churn-grounded-agent.yaml`) enforced. Proves the reference implementation's Foundry/Databricks dependencies are expressed entirely through intended project configuration — not hidden factory wiring — and that the governed assistant contract already declared in this repo is actually exercised, not merely validated as a static contract.
- **R3.6 — Migration closure / retirement gate.** Unchanged: confirm no R3/R4 workload depends on the old (cross-tenant) Databricks environment, archive provenance evidence, retire or quarantine it, document the migration decision and rollback boundary.

## R3 acceptance test

> Take the known-working reference implementation, migrate it to the target architecture, and demonstrate that it operates independently using only the identities, infrastructure, integrations, and configuration contracts that a generated project is supposed to have.

R3 is complete when this test passes — not when each individual technology is separately shown to work, since that was already true before R3 began.

## Related documents

- `docs/decisions/0011-factory-reference-boundary.md` — factory/generated-project/proving-ground roles, no-accidental-inheritance invariant.
- `docs/decisions/0012-platform-foundation-state-boundary.md` — Terraform state separation.
- `docs/decisions/0014-factory-generated-project-identity-separation.md` — the identity-sharing rule this document's Runtime identity row applies for the second time (GitHub deploy identity in R3.2, reference-runtime identity in R3.3).
- `docs/architecture/resource-ownership.md` — the live, verified resource-ownership matrix this document's Gap analysis table summarizes at the architecture-domain level.
- `docs/superpowers/plans/r3.2-platform-foundation.md` — R3.2's execution log and closure evidence.
