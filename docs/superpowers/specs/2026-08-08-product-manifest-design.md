# Product Manifest Schema — Design Spec

## Status

Draft — pending user review.

## Context

The long-term goal is a configuration-driven "AI factory": for every new product, autogenerate as much as possible from a declarative configuration, with a containerized model-lifecycle CI/CD pipeline orchestrated by AKS, configurable-but-guarded security posture, and the churn scenario shipping as the reference implementation the template produces when nothing is customized. Each product is a separate repo (to support portfolio-level reporting), consuming `platform_core` as a versioned dependency rather than a copied file tree, so platform invariants stay enforced instead of drifting per repo.

That vision decomposes into five independent sub-projects:

1. **Unified product manifest schema** — this spec.
2. `platform_core` distribution model (packaged, versioned dependency).
3. The factory/generator tool that stamps out a new product repo from a manifest.
4. AKS-coordinated containerized CI/CD for the model lifecycle. Primary driver is enterprise-scale capacity — the scaffolding needs to scale the way large enterprises demand; centralized CI/CD monitoring and control is a side benefit, not the reason AKS is there. Confirmed scope: **orchestrator only** — it coordinates pipeline steps as containers; Databricks remains the compute/serving authority; Container Apps remains the application plane.
5. Portfolio-level reporting/aggregation across products.

This spec covers only #1: the schema that will drive #2–#5.

## Goals

- Define one versioned, validated `ProductManifest` contract in `platform_core` that fully describes a product: data source/contract, features, candidate models, evaluation/promotion policy, serving, retrieval wiring, agent behavior/tools, model routing, and per-environment security posture.
- Ensure the schema is proven against a real, working product (the churn scenario currently shipped in this repo) without embedding any knowledge of churn inside `platform_core` itself. Churn is the first product built on the schema, not a special case of it — `platform_core` must never reference "churn," or any other scenario name, anywhere in its own source or test suite (this is a restatement of the existing invariant in `docs/template/architecture.md`: "No scenario data, model, customer, or endpoint names are hardcoded in `platform_core`," applied to tests as strictly as to runtime code).
- Churn is defined entirely by its config files. If a team overwrites those files with their own product's configuration, churn simply no longer exists in that repo — no fallback or reconstruction logic anywhere depends on it being present.
- Make the production security posture structurally safe regardless of what an individual product repo's config requests.
- Retire `platform_core.settings.config.Settings`'s existing hardcoded churn-specific defaults (`model_serving_endpoint`, `databricks_catalog`, `feature_schema_version`, `feature_contract` — a pre-existing instance of the same hardcoding problem, found while implementing this spec) so those values are derived from `ProductManifest` at runtime instead.

## Non-goals (deferred to later sub-projects or out of scope entirely)

- `platform_core` packaging/publishing mechanics (#2).
- The generator/factory tool itself — how it scaffolds a repo, prompts for overrides, wires CI (#3).
- AKS pipeline definition/manifests (#4) — may reference this schema later, not designed here.
- Portfolio reporting's data model and read surface (#5).
- Retrieval infrastructure — index build/refresh jobs, embedding model choice, chunking strategy, vector store selection. This is template-owned machinery living in the existing Data/ML plane pipeline (`ingest → validate → bronze → silver → gold/features → …`), not something a product manifest defines. The manifest only declares which indexes exist and which agent tools consume them.
- Manifest schema migration tooling across `manifest_version` bumps — only exact-version validation is handled now; add migration tooling when a second version actually exists.

## Architecture

### File layout

```
src/scenarios/<name>/
  product.yaml          # new — identity, manifest_version, environments, security posture
  scenario.yaml         # existing — data contract, features, evaluation, promotion, serving, retrieval
  config.yaml           # existing, narrowed — per-environment resolved values only
  routing.yaml          # new — foundation model selection per environment
foundry/agents/<name>.yaml       # existing, unchanged — prompt, tools, guardrails, output schema
foundry/tools/tools.contract.json # existing, unchanged — allowlisted tool contract
```

No path-pointer indirection: the generator, CI, and the `ProductManifest` loader all know these fixed, conventional paths. `platform_core` gains one new model, `ProductManifest`, that loads `product.yaml` plus all section files for a given scenario directory and validates them as a single object. This is the object consumed downstream by the factory generator (#3), the AKS pipeline (#4), and the portfolio reporter (#5).

### `product.yaml` (new)

```yaml
product:
  name: churn
  display_name: "Telco Churn Reference"
  manifest_version: "1.0"
environments: [dev, test, prod]
security:
  dev:  { agent_data_access: mediated }
  test: { agent_data_access: mediated }
  prod: { agent_data_access: mediated }
```

- `agent_data_access` ∈ {`mediated`, `direct`}. `mediated` means Foundry agents only reach data through the allowlisted, read-only application tools (today's design — `get_customer_score`, `get_customer_diff`, `retrieve_customer_evidence`, `retrieve_playbooks`). `direct` is a future escape hatch, not implemented today.
- **`prod` can never validate as `direct`.** This is enforced in `platform_core`'s shared validator code, not left to per-product config — loosening it requires a `platform_core` code change (and version bump) that every product opts into deliberately, matching the existing invariant phrasing ("unless a future ADR explicitly changes that policy"). `dev`/`test` may set `direct` freely since those environments already get isolated, non-prod data.

### `scenario.yaml` (existing — retrieval section enriched, everything else unchanged)

```yaml
retrieval:
  vector_indexes:
    - name: notes_vs
      source_table: gold.customer_notes
      used_by: [retrieve_customer_evidence]
    - name: tickets_vs
      source_table: gold.support_tickets
      used_by: [retrieve_customer_evidence]
    - name: playbooks_vs
      source_table: gold.recommended_actions
      used_by: [retrieve_playbooks]
```

`used_by` cross-references tool names declared in `tools.contract.json`. This lets the validator catch two classes of drift: an index nothing consumes, or a tool that claims retrieval with no backing index. `name`/`task`/`source_datasets`/`evaluation`/`promotion_policy`/`serving` keep their current shape. `features` is unchanged. A new `model` block is added (relocated from `config.yaml` — see below, these fields are not duplicates, just misplaced today):

```yaml
model:
  name: churn_classifier
  candidate_models: [logistic_regression, random_forest]
  minimum_rows: 7043
```

### `config.yaml` (existing — narrowed)

Today this file duplicates `task_type`, `feature_schema_version`, `feature_contract`, `model.primary_metric`, and `model.minimum_improvement`, all of which already live in `scenario.yaml` (the last two as `promotion_policy.metric`/`promotion_policy.threshold`). Those five are removed. Everything else in `config.yaml` is genuinely not duplicated anywhere — including `model.name`, `model.candidate_models`, and `model.minimum_rows`, which are relocated to `scenario.yaml`'s new `model` block above rather than deleted, since they describe the ML contract, not a per-environment/ingestion value:

```yaml
scenario: churn
source_dataset: telco_customer_churn_v1
source_url: https://raw.githubusercontent.com/IBM/telco-customer-churn-on-icp4d/master/data/Telco-Customer-Churn.csv
expected_customer_count: 7043
catalogs:
  dev: mlworkflow_dev
  test: mlworkflow_test
  prod: mlworkflow_prod
schemas: [bronze, silver, gold, ml, ops]
playbooks_table: gold.recommended_actions
```

`config.yaml`'s remaining purpose: data ingestion and runtime resolution parameters (source location, expected volume, per-environment catalog names, schema list) — not the ML contract itself.

### `routing.yaml` (new)

Deliberately minimal — a primary deployment plus an ordered fallback list per environment. No rule-based or dynamic routing engine; nothing in scope has asked for more than "pick a model, fall back on failure."

```yaml
dev:
  primary: gpt-4o-mini
  fallback: []
test:
  primary: gpt-4o-mini
  fallback: []
prod:
  primary: gpt-4o
  fallback: [gpt-4o-mini]
```

Schema validates shape only (`primary` non-empty, `fallback` a list). Whether a named deployment actually exists in the Foundry catalog is a deploy-time check owned by the factory generator (#3) and AKS pipeline (#4), not something `platform_core` can know statically.

### `foundry/agents/<name>.yaml`, `foundry/tools/tools.contract.json`

Unchanged in shape. Now participate in `ProductManifest` validation via the `retrieval.used_by` cross-reference above.

## Validation rules (`ProductManifest` in `platform_core`)

- `manifest_version` must exactly match the version the installed `platform_core` supports. Mismatch fails validation with an explicit "upgrade platform_core" message. No migration layer yet.
- `security.prod.agent_data_access` can never be `direct` — hard-coded in the shared validator, not configurable per product.
- Full reciprocity between retrieval and tools: every `retrieval.vector_indexes[].used_by` entry must reference a tool name present in `tools.contract.json`, and every tool name that appears in any index's `used_by` list must exist in `tools.contract.json`. An index with an empty `used_by` (dead index) or a retrieval tool referenced by no index (no backing data) both fail validation.
- `routing.<env>.primary` required and non-empty for every environment listed in `product.yaml`'s `environments`.
- All validation is load-time and fail-fast — no partial acceptance of an invalid manifest.

## Defaults mechanism: copy-on-generate, not runtime merge

Because this is explicitly a template, "not customized" means the section files are still byte-for-byte what the factory generator (#3) copied from churn's own files at repo-generation time. There is no deep-merge/fallback engine that resolves missing product fields against churn's values at runtime — that mechanism would add real complexity (merge precedence, scalar-vs-list rules, "where did this value come from" debugging) to solve a problem copy-then-edit already solves. `platform_core`'s only schema-level defaults are generic and non-domain (`manifest_version` current version, empty `fallback` list) — never domain values like row counts or model names, so nothing a reviewer sees is implicit.

**Acceptance criterion:** churn's own section files must validate cleanly against `ProductManifest`, proven by a test in *this repo's* test suite (not `platform_core`'s package test suite — see Testing strategy). This guarantees the schema can never drift from what the template actually ships, without making `platform_core` depend on churn existing.

## Error handling

- Validation failures are load-time and fail-fast, with a message identifying the file, field, and reason.
- A `manifest_version` mismatch blocks pipeline entry with an explicit upgrade instruction rather than attempting to coerce or ignore the mismatch.
- No silent fallback and no partial acceptance of an invalid manifest at any stage.

## Testing strategy

Two separate test surfaces, deliberately not mixed:

- **`platform_core` package tests** (ship with the package, run against every consumer): exercise `ProductManifest`'s validation rules using small, synthetic, made-up fixtures — no scenario names, no churn. This is what keeps `platform_core` provably domain-neutral. Covers: `prod` + `agent_data_access: direct` rejected; `retrieval.used_by` / tool cross-reference catches both drift directions; `manifest_version` mismatch rejected; missing `routing.<env>.primary` rejected.
- **This repo's own test suite** (consumer-side, same as any other product repo would have): a contract test that loads churn's real, checked-in section files through `platform_core`'s `ProductManifest` and asserts they validate. Any future edit to churn's files that breaks this is a regression in *this repo*, not in `platform_core`. If churn's files are ever replaced by a different product's configuration, this test simply becomes that product's own manifest test — nothing about it assumes churn specifically.

## Open questions / follow-ups for later sub-projects

- Whether the factory generator (#3) copies files verbatim and lets a team edit them directly, or also offers an interactive override prompt at generation time. Whatever it does, it must treat the example product directory as plain data to copy, not as named/hardcoded logic — the generator shouldn't know the word "churn" any more than `platform_core` does.
- Whether `routing.yaml` later needs a section-file reference from an AKS pipeline manifest (#4) once that sub-project is designed.
- What surface each product must expose for portfolio reporting (#5) to read from.

## Documentation changelog

| Version | Created | Modified | Who | Notes |
|---|---|---|---|---|
| 0.1.0 | 2026-08-08 | 2026-08-08 | Ray Swan / Claude | Initial product manifest schema design spec (AI factory sub-project #1). |
