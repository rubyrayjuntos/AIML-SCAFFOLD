# ADR 0009: R1 deployment-plan governance

## Decision

Every R1 generated Azure ML batch repository contains `.azure/deployment-plan.md`. The factory creates deterministic initial content with status `Planning`; Azure preparation and validation then update the document with live, sanitized validation evidence and advance its status through the documented workflow.

`.azure/deployment-plan.md` and `.azure/validate-status.json` are mutable governance evidence. They are excluded from the deterministic generated-files digest because their status and proof necessarily change after generation. They remain governed in four ways:

1. The deterministic deployment-plan template is included in the platform template digest.
2. The generated product source commit records the exact validated files reviewed by protected PR and CI.
3. Saved-plan creation requires deployment-plan status `Validated` and validation workflow completion at `UpdateStatus`.
4. The saved-plan approval metadata and artifact manifest record SHA-256 digests of both governance files; apply rechecks those digests from the recorded product commit.

Saved-plan production must fail when the plan is absent, not validated, contains incomplete proof markers, or the validation status does not record `UpdateStatus`. A governance-only source change still changes the product commit and requires a new saved plan.

This contract does not authorize Terraform apply. Apply remains a separate deliberate, digest-bound owner decision against one reviewed artifact and unchanged remote-state identity.

## Consequences

- Every future generated project enters the same preparation and validation gate.
- Runtime validation evidence does not make generation nondeterministic.
- A generation ID alone is insufficient to authorize apply; product commit and governance digests are also mandatory.
- Validation proof may not contain tokens, signed URLs, raw environment dumps, or credentials.
- The deployment plan remains Terraform-only for R1 and cannot introduce azd, Bicep, bootstrap, Test, Prod, or Azure ML workload execution.

## Documentation changelog

| Version | Created | Modified | Who | Notes |
|---|---|---|---|---|
| 1.0.0 | 2026-08-12 | 2026-08-12 | Ray Swan / Codex | Established deterministic generation, mutable validation evidence, protected-source binding, and saved-plan digest enforcement. |
