# ADR 0011: Factory/reference-product boundary and the no-accidental-inheritance invariant

## Decision

AIML-SCAFFOLD is an implementation-partner accelerator for Azure AI/ML, not an Azure MLOps v2 reimplementation. Azure (and Databricks, Foundry, etc. within it) is the capability surface; this repository is the opinionated composition layer that turns that surface into a coherent, generatable starting architecture — the same role a Salesforce implementation partner's starter store plays relative to the Salesforce platform.

Three roles are kept explicitly separate:

- **The factory floor** (this repository): the generator, templates, platform contracts, validation machinery, and the `churn` reference implementation used to prove templates against live Azure before they are trusted.
- **The generated car**: a project repo produced by the generator. Self-contained — application code, project-specific Terraform, workflows, lifecycle logic, configuration, evidence conventions. It does not live inside, or run inside, the factory.
- **Azure as proving ground**: the primary subscription hosts a live reference deployment so the factory can prove real identity, RBAC, networking, and service-to-service integration — not just offline Jinja templates. Evidence from that live proof feeds back into the factory's templates.

`azure-mlops` (a separate, earlier standalone repo) is historical prior art from before this boundary was established. It is not a second active architectural center and is not part of R3's consolidation target.

## The no-accidental-inheritance invariant

Generated projects may inherit architecture and configuration **contracts** from the factory (patterns, defaults, module shapes), but never an undeclared **runtime dependency** on a factory-owned resource. A generated project must either provision its own equivalent resource, or explicitly declare consumption of a named, intentionally shared platform service. It must never silently point back at the factory's own reference Databricks workspace, Foundry deployment, or any other factory-owned live resource.

This directly generalizes the failure mode diagnosed during R3 Slice 1: the churn reference reached for Databricks on a subscription/tenant that had no declared relationship to the primary platform subscription, producing manual, ad hoc cross-tenant auth handling instead of a governed dependency.

## Rationale

Microsoft's own accelerator can only offer capability, not opinion — it has too many customers with too many divergent needs to be strongly prescriptive. An implementation partner can and must be opinionated: defaults, contracts, optional modules, and escape hatches, encoded once so every future engagement doesn't re-derive them. The three-repository structure common to Azure MLOps v2-style accelerators was a symptom of treating Azure capability enumeration as if it were the product; this project treats the *opinionated composition* as the product, with Azure underneath it as substrate.

The target is not empty scaffolding — it is the equivalent of a Salesforce Commerce "starter store": a working, full-featured reference product, not a rebuild-from-scratch starting point. An implementation partner never rebuilds commerce from zero; they start from that working foundation and add accelerators so each new engagement becomes progressively more configurable rather than progressively more custom-coded. A generated project should already have a working, governed foundation across infrastructure/identity, CI/CD and deployment governance, ML lifecycle and promotion, retrieval and agent architecture, evidence and provenance, observability, and cost-aware compute — with the differences *between* projects living in configuration, not bespoke engineering.

The factory's success condition is therefore a progression, not a single destination: implementation variability moves from code, to configuration, to **business-accessible configuration** — capability toggles, model/prompt selection, evaluation criteria, data sources, agent tools and policies, promotion thresholds, and operational policies that a business user can set without a developer in the loop. The factory is not fully succeeding merely because developers generate projects faster; it succeeds when many implementation choices stop requiring a developer at all.

## Consequences

- R3 is redefined as "subscription consolidation + shared AI platform foundation," not "add Databricks and Foundry." Its acceptance criterion is that the factory's reference architecture composes real Azure services under one governed identity boundary — see the R3 slice breakdown in `docs/decisions/` history / project memory for the current plan.
- Every future resource the factory provisions for its own reference proof must be classified: factory-owned, generated-project-owned, or shared-service candidate. R3.1's target-state inventory introduces this classification as a resource ownership matrix; later resources should be classified at creation time, not retrofitted.
- A generated project's manifest may declare that it *consumes* a shared platform service, but the factory must never make that the only path — an equivalent self-provisioned option must exist, or the "opinionated but not a single-use-case template" balance is broken.
- `azure-mlops` remains available for provenance and for rescuing known-good implementation details, but no R3+ decision should be designed around preserving compatibility with it.

## Documentation changelog

| Version | Created | Modified | Who | Notes |
|---|---|---|---|---|
| 0.2.0 | 2026-08-17 | 2026-08-17 | Ray Swan / Claude | Corrected the Salesforce analogy: the target is a working starter-store-equivalent reference product, not scaffolding. Added the code-to-configuration-to-business-accessible-configuration progression as the factory's actual success criterion. |
| 0.1.0 | 2026-08-17 | 2026-08-17 | Ray Swan / Claude | Initial record of the factory/reference/shared-service boundary and the no-accidental-inheritance invariant, established while redefining R3. |
