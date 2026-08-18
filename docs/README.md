# Documentation index

This is the map of `docs/`. If you're adding a new document and aren't sure where it belongs, use the taxonomy below as the rule of thumb. If you're looking for "why did we decide X," check `docs/decisions/` first — see [`AGENTS.md`](../AGENTS.md).

## Taxonomy — where new docs go

- **`docs/decisions/`** — point-in-time Architecture Decision Records (ADRs). Immutable once accepted; a later document may add an explicit "superseded by ADR-NNNN" note, but an ADR is never edited to reflect new understanding. If the reasoning changed, write a new ADR.
- **`docs/architecture/`** — the living description of current-state architecture and evidence. Edited in place as the system evolves. Cites ADRs by link rather than restating their reasoning.
- **`docs/template/`** — the shape of the generatable template itself, as consumed by someone building a project *from* this factory (as opposed to this repo's own architecture).
- **`docs/runbooks/`** — operational how-to: imperative steps, minimal rationale.
- **`docs/superpowers/plans/`** — disposable, dated, one-off implementation plans for a specific slice of work. Once executed, a plan should eventually be archived or deleted, not left indefinitely alongside still-relevant docs.
- **`docs/scenarios/<name>/`** — everything specific to one reference scenario (e.g. `churn`).
- **`docs/demo/`** — cross-scenario demo scripts.

## Current contents

### `docs/decisions/` — ADRs

- `0001-authoritative-iac.md`
- `0002-template-scenario-boundary.md`
- `0003-capability-maturity.md`
- `0004-project-evidence-store.md`
- `0005-r1-project-topology.md`
- `0006-r1-provenance-and-provider-extensions.md`
- `0007-r1-azure-context-and-doctor.md`
- `0008-r1-digest-bound-approval.md`
- `0009-r1-deployment-plan-governance.md`
- `0010-r1-local-first-compute-policy.md`
- `0011-factory-reference-boundary.md`
- `0012-platform-foundation-state-boundary.md`
- `0013-product-manifest-design-superseded.md`

### `docs/architecture/` — living architecture and evidence

- `overview.md` — canonical architecture overview.
- `security.md` — canonical security architecture.
- `resource-ownership.md`
- `environment-strategy.md`
- `azure-ml-capability-ledger.md`
- `r1-compatibility-matrix.md`
- `r1-dev-evidence-matrix.md`
- `r1-evidence-ledger.md`

### `docs/template/` — template shape

- `architecture.md`
- `security.md`
- `configuration.md`
- `deployment.md`
- `extension-guide.md`
- `identity-and-environments.md`
- `lifecycle.md`
- `operations.md`
- `tooling.md`

### `docs/runbooks/` — operational how-to

- `local-validation.md`
- `model-promotion.md`
- `r1-bootstrap-deployment.md`
- `r1-deployment-plan.md`
- `r1-local-generation.md`

### `docs/scenarios/churn/` — churn reference scenario

- `README.md`
- `data-contract.md`
- `demo-runbook.md`
- `evaluation.md`
- `feature-catalog.md`

### `docs/demo/` — cross-scenario demo scripts

- `interview-flow.md`

### `docs/superpowers/plans/` — disposable dated plans

- `2026-08-08-product-manifest-schema.md`
- `r3.2-platform-foundation.md`

These are working plans for in-flight or recently completed slices of work. Once a plan's work is executed and evidenced elsewhere (an ADR, an architecture doc, a runbook), the plan file itself should be archived or deleted rather than kept as a second copy of the truth.

## Documentation changelog

| Version | Created | Modified | Who | Notes |
|---|---|---|---|---|
| 1.0.0 | 2026-08-17 | 2026-08-17 | Ray Swan / Claude | Initial documentation index: taxonomy rule of thumb plus current contents of `docs/decisions/`, `docs/architecture/`, `docs/template/`, `docs/runbooks/`, `docs/scenarios/`, `docs/demo/`, and `docs/superpowers/plans/`. |
