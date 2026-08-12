# ADR 0008: R1 digest-bound manual deployment approval

## Decision

R1 generated repositories implement `manual_dispatch_with_plan_digest` as an external manual authorization contract:

1. A manually invoked plan workflow verifies generation provenance, creates one binary Terraform plan, and publishes it with the source commit, generation ID, manifest digest, resolved-plan digest, environment, run identity, and plan digest.
2. A separately invoked apply workflow requires the plan run ID, run attempt, exact reviewed SHA-256 digest, and an environment-specific confirmation phrase.
3. Apply downloads that artifact, validates its closed file set and metadata, checks out the recorded source commit, re-verifies generation provenance, and applies the downloaded plan without replanning.
4. No generated workflow applies Terraform on `push` or `pull_request`.

The contract provides a deliberate human action and immutable-plan binding. When one human is the only operator, it does not claim independent reviewer separation of duties.

Native GitHub environment required-reviewer enforcement remains preferred where the repository plan supports it. Protected-branch policy alone is not represented as manual deployment approval.

## Consequences

- The exact plan reviewed is the plan applied.
- Plan and apply executions have durable GitHub run and artifact correlation.
- Artifact expiry or deletion requires a new plan and review; it must never trigger replanning inside apply.
- Initial source publication, branch protection, OIDC proof, workload planning, and workload apply remain distinct gates.
- R1 release evidence must identify whether approval was native, digest-bound manual dispatch, or an approved external control.

## Documentation changelog

| Version | Created | Modified | Who | Notes |
|---|---|---|---|---|
| 0.1.0 | 2026-08-12 | 2026-08-12 | Ray Swan / Codex | Selected digest-bound separate plan/apply dispatch as the R1 fallback when native required reviewers are unavailable. |
