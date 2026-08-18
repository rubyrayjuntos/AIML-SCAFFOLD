# ADR 0013: Product manifest design spec superseded by the factory/reference boundary

## Decision

The original 2026-08-08 product-manifest design spec (formerly `docs/superpowers/specs/2026-08-08-product-manifest-design.md`, retired as part of the `docs/superpowers/specs/` category being closed) is retained here as historical context rather than deleted outright. Its file-layout, schema, and validation content remains substantially accurate and implemented; only its framing of "the product" and "the template" needs the correction ADR 0011 later supplied. This ADR does not reopen or amend ADR 0011 — it records what the spec proposed, and how ADR 0011's factory/generated-project/proving-ground terminology supersedes and refines it.

### What the original spec proposed

The spec covered sub-project #1 of a five-part "AI factory" vision: a single versioned, validated `ProductManifest` contract in `platform_core` that fully describes a product — data source/contract, features, candidate models, evaluation/promotion policy, serving, retrieval wiring, agent behavior/tools, model routing, and per-environment security posture. Its core design commitments:

- **File layout.** `product.yaml` (new — identity, `manifest_version`, environments, security posture), `scenario.yaml` (existing, enriched with a `retrieval` section and a relocated `model` block), `config.yaml` (existing, narrowed to ingestion/runtime-resolution values only), and `routing.yaml` (new — a primary foundation-model deployment plus an ordered fallback list per environment, deliberately minimal with no rule-based routing engine).
- **Domain neutrality invariant.** `platform_core` must never reference "churn," or any other scenario name, in its own source or test suite — extending the existing `docs/template/architecture.md` invariant ("no scenario data, model, customer, or endpoint names are hardcoded in `platform_core`") to test code as strictly as runtime code. Churn is defined entirely by its config files; if a team overwrites those files with their own product's configuration, churn simply no longer exists in that repo.
- **Structural production safety.** `security.prod.agent_data_access` can never validate as `direct` — hard-coded in `platform_core`'s shared validator, not left to per-product config, so loosening it requires a deliberate `platform_core` version bump every product opts into.
- **Retrieval/tool reciprocity.** Every `retrieval.vector_indexes[].used_by` entry must reference a real tool in `tools.contract.json`, and every tool claiming retrieval must be backed by an index — catching both a dead index and an unbacked tool.
- **Defaults as copy-on-generate, not runtime merge.** "Not customized" means the section files are still byte-for-byte what the generator copied from churn's files at generation time. There is no deep-merge/fallback engine resolving missing product fields against churn's values at runtime; `platform_core`'s only schema-level defaults are generic and non-domain (current `manifest_version`, empty `fallback` list).
- **Two-tier testing.** `platform_core` package tests exercise validation rules against small synthetic fixtures with no scenario names; this repo's own test suite runs a contract test that loads churn's real, checked-in section files through `ProductManifest` and asserts they validate — a regression in this repo if churn's files ever break it, not in `platform_core`.
- **Explicit non-goals**, deferred to four sibling sub-projects the spec named but did not design: `platform_core` packaging/publishing, the generator/factory tool itself, AKS-coordinated containerized CI/CD for the model lifecycle (scoped even then as orchestrator-only — Databricks remains the compute/serving authority, Container Apps remains the application plane), and portfolio-level reporting across products.

### How ADR 0011 supersedes and refines it

ADR 0011 was written after the R3 Slice 1 failure mode — a generated project silently reaching for a factory-owned Databricks workspace on an undeclared tenant/subscription relationship — exposed that "product," "template," and "the repo" were being used ambiguously across the codebase. It formalizes three roles this spec's language never separated:

- **The factory floor** (this repository): the generator, templates, platform contracts, validation machinery, and the churn reference implementation used to prove templates against live Azure.
- **The generated car**: a project repo the generator produces — self-contained, not living or running inside the factory.
- **Azure as proving ground**: the live reference deployment that proves real identity, RBAC, networking, and integration, feeding evidence back into the factory's templates.

The spec's "product" was really describing what ADR 0011 calls the generated car's configuration surface, and its "platform_core" was the factory floor's contract layer — the spec got the mechanism right (`ProductManifest` as the single validated description a generated project's own files satisfy) but didn't yet have names for the boundary it was implicitly enforcing. Concretely:

- The spec's domain-neutrality invariant ("`platform_core` must never reference churn") is a specific instance of ADR 0011's no-accidental-inheritance invariant: a generated project may inherit contracts (patterns, defaults, module shapes) from the factory, but never an undeclared runtime dependency on a factory-owned resource. The spec enforced this only at the schema/test level; ADR 0011 generalizes it to every resource class (Databricks, Foundry, storage, identity).
- The spec's "if a team overwrites churn's config files, churn simply no longer exists in that repo" is exactly ADR 0011's generated-car self-containment property, stated a layer down (config files instead of the whole repo).
- The spec's copy-on-generate defaults mechanism is the concrete implementation of what ADR 0011 later named the factory-floor-to-generated-car handoff: contracts and shapes transfer at generation time; nothing about a generated project's runtime behavior silently depends on the factory afterward.
- The spec's four deferred sub-projects (generator, AKS pipeline, packaging, portfolio reporting) are each, in ADR 0011's terms, factory-floor machinery that must classify every resource it touches as factory-owned, generated-project-owned, or shared-service candidate — a classification discipline the spec did not yet have language for.

Nothing in the spec's technical design (schema shape, validation rules, file layout, testing strategy) is invalidated by ADR 0011. What ADR 0011 supersedes is purely the vocabulary: "product manifest" work should now be read and extended using the factory/generated-project/proving-ground framing, not the spec's original undifferentiated "product" and "platform_core" language.

## Rationale

ADRs are point-in-time and immutable; ADR 0011 must not be retroactively edited to absorb this history. But deleting the original spec outright (as part of retiring `docs/superpowers/specs/` as a standing category — the directory held exactly one file and was not being populated further) would discard genuinely load-bearing design content: the file layout, the reciprocity validation rule, the copy-on-generate defaults reasoning, and the two-tier testing split are all still the actual shape of the implemented schema. Recording this as a companion ADR to 0011 preserves that content where future readers of the factory/reference boundary decision will naturally look, without pretending the spec was wrong on its merits or silently losing it.

## Consequences

- `docs/superpowers/specs/2026-08-08-product-manifest-design.md` is deleted; this ADR is its permanent historical record.
- Future work on `ProductManifest`, `product.yaml`, `routing.yaml`, or the retrieval/tool reciprocity rule should cite this ADR and ADR 0011 together, not the retired spec file.
- No schema, validator, or test behavior changes as a result of this ADR — it is a documentation-lineage correction only.

## Documentation changelog

| Version | Created | Modified | Who | Notes |
|---|---|---|---|---|
| 0.1.0 | 2026-08-17 | 2026-08-17 | Ray Swan / Claude | Created as the historical companion record to ADR 0011, preserving the retired `docs/superpowers/specs/2026-08-08-product-manifest-design.md` design content and explaining how ADR 0011's factory/generated-project/proving-ground framing supersedes and refines it. |
