## Project

Azure-first, config-driven enterprise ML workflow template (`enterprise-ml-workflow`). The reusable platform is the primary product; Telco churn is one executable reference scenario built on top of it — not the other way around. Independent of, and must never reuse code/data/schemas/model registry/deployment state from, the legacy `cust-churn` project.

## Source map

- `src/platform_core/` — domain-neutral contracts, orchestration, lifecycle, lineage, evaluation gates, observability, integrations. Must never hardcode scenario (churn) names/data/models.
  - `contracts/models.py`, `lifecycle/aliases.py`, `lineage/metadata.py`, `evaluation/gates.py`, `settings/config.py`, `integrations/databricks_serving.py`
- `src/scenarios/churn/` — churn-specific scenario manifest (`scenario.yaml`) and config (`config.yaml`). Scenario adapter code is expected/allowed to be more verbose than platform_core.
- `src/api/app.py` — FastAPI application (application plane).
- `infra/` — Bicep (authoritative IaC) and Terraform (portability-only, separate resource group/state, never overlaps Bicep-managed resources) — see `mem:invariants`.
- `databricks/` — Databricks Asset Bundles.
- `docs/template/` — platform-wide docs (architecture, configuration, deployment, lifecycle, security, tooling, identity-and-environments, extension-guide, operations).
- `docs/scenarios/churn/` — churn scenario docs (data contract, feature catalog, evaluation, demo runbook).
- `docs/decisions/` — ADRs (0001 Bicep authoritative, 0002 template/scenario boundary).

## Key references

- Non-negotiable platform invariants and pipeline stages: `mem:invariants`
- Tech stack, dependency groups: `mem:tech_stack`
- Commands for validation/dev: `mem:suggested_commands`
- Task-done checklist: `mem:task_completion`
- Documentation conventions (every .md needs a versioned changelog table): `mem:conventions`
