# ADR 0008: R1 digest-bound manual deployment approval

## Decision

R1 generated repositories implement `manual_dispatch_with_plan_digest` as an external manual authorization contract:

1. A manually invoked plan workflow verifies generation provenance, creates one binary Terraform plan, derives a structurally sanitized JSON representation with the same Terraform version, and publishes the closed schema `1.0` artifact set: `r1.tfplan`, `r1.tfplan.sha256`, `r1-plan.sanitized.json`, `r1-plan.sanitized.json.sha256`, `approval-metadata.json`, and `artifact-manifest.v1.json`.
2. A separately invoked apply workflow requires the plan run ID, run attempt, exact reviewed SHA-256 digest, and an environment-specific confirmation phrase.
3. Apply downloads that artifact; rejects missing, additional, malformed, duplicate, digest-conflicting, run-conflicting, environment-conflicting, backend-conflicting, or action-summary-conflicting evidence; checks out the recorded source commit; re-verifies generation provenance; and applies the downloaded plan without replanning.
4. No generated workflow applies Terraform on `push` or `pull_request`.

The contract provides a deliberate human action and immutable-plan binding. When one human is the only operator, it does not claim independent reviewer separation of duties.

Native GitHub environment required-reviewer enforcement remains preferred where the repository plan supports it. Protected-branch policy alone is not represented as manual deployment approval.

## Consequences

- The exact plan reviewed is the plan applied.
- The binary digest binds the executable plan and the JSON digest binds its human-reviewable representation. Raw Terraform JSON is ephemeral and never uploaded.
- Runtime timestamps exist only in the artifact manifest and do not participate in deterministic generated-source identity.
- Plan and apply executions have durable GitHub run and artifact correlation.
- Artifact expiry or deletion requires a new plan and review; it must never trigger replanning inside apply.
- Initial source publication, branch protection, OIDC proof, workload planning, and workload apply remain distinct gates.
- R1 release evidence must identify whether approval was native, digest-bound manual dispatch, or an approved external control.

## Documentation changelog

| Version | Created | Modified | Who | Notes |
|---|---|---|---|---|
| 0.2.0 | 2026-08-12 | 2026-08-12 | Ray Swan / Codex | Versioned the six-file plan artifact, structural sanitization, dual digests, backend/provenance binding, and action-summary verification. |
| 0.1.0 | 2026-08-12 | 2026-08-12 | Ray Swan / Codex | Selected digest-bound separate plan/apply dispatch as the R1 fallback when native required reviewers are unavailable. |
