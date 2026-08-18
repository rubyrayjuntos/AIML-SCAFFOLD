# Template deployment

## Ownership

Terraform is the authoritative generated Azure deployment path for R1. Existing Bicep is an experimental reference and must never manage an R1 Terraform resource group or any Terraform-owned resource.

The generated repository consumes an administrator-created resource group, remote Terraform backend, OIDC identity, and scoped grants. The generated deployment identity does not require subscription-level Owner. Databricks deployment is outside R1.

## Deployment sequence

1. Validate and resolve the manifest without cloud operations.
2. Generate into an empty directory and verify the generation receipt.
3. Run `aiml-scaffold doctor` in offline mode, then authenticated read-only mode.
4. Complete `.azure/deployment-plan.md` through the documented Azure validation workflow. Saved-plan production requires status `Validated` and `.azure/validate-status.json` completion at `UpdateStatus`.
5. Publish the exact validated product source through protected PR and CI, then authenticate GitHub Actions with Entra OIDC.
6. Run and review the Dev Terraform plan and its complete six-file schema `1.0` review artifact.
7. Apply Terraform only through the separate digest-bound manual workflow using the reviewed plan artifact. The apply workflow must never replan.
8. Run Azure ML training, evaluation, and conditional registration.
9. Deploy an explicit registered model version to the batch endpoint.
10. Invoke the endpoint and independently verify evidence and outputs.
11. Regenerate without source edits and require a clean second Terraform plan.

## Enterprise integration

The R1 manifest references centrally administered Terraform state and identity prerequisites. Each environment owns an independent Azure ML workspace, storage boundary, evidence container, and Terraform state key.

No R1 CLI command deploys or destroys resources. Failure rollback preserves Terraform state and evidence. Any corrective apply or disposable-environment destroy requires a reviewed plan and explicit approval.

When native GitHub required reviewers are unavailable, R1 uses `manual_dispatch_with_plan_digest`: the plan workflow publishes the binary plan, its structurally sanitized JSON representation, dual digests, approval metadata, and a versioned artifact manifest. The manifest also records expiry, platform package/source provenance, Azure context, and the pre-plan state lineage, serial, and digest. Apply requires both reviewed digests, an allowlisted actor, approval reason, source and generation identities, target environment, unchanged Azure/backend state, consistent action summary, and confirmation phrase. It records a sanitized GitHub apply-result artifact before relying on project-local evidence. This is deliberate manual authorization, but it does not claim independent separation of duties when one person is the only operator.

The generated deployment plan and validation-status file are mutable validation evidence rather than deterministic generated content. Their template is covered by platform provenance; their final content is bound by the protected product commit and by explicit SHA-256 fields in every saved-plan artifact. Changing either file after planning invalidates apply verification.

## Documentation changelog

| Version | Created | Modified | Who | Notes |
|---|---|---|---|---|
| 0.6.0 | 2026-08-07 | 2026-08-12 | Ray Swan / Codex | Required validated deployment-governance evidence before planning and bound its final digests to the saved artifact and apply verifier. |
| 0.5.0 | 2026-08-07 | 2026-08-12 | Ray Swan / Codex | Bound apply to platform provenance, artifact age, Azure context, unchanged backend state, dual reviewed digests, allowlisted actor, approval reason, and durable result evidence. |
| 0.4.0 | 2026-08-07 | 2026-08-12 | Ray Swan / Codex | Required the schema 1.0 six-file saved-plan artifact and apply-side provenance, backend, digest, and action verification. |
| 0.3.0 | 2026-08-07 | 2026-08-12 | Ray Swan / Codex | Defined digest-bound manual plan/apply authorization without replanning or an unsupported independent-reviewer claim. |
| 1.0.0-rc1 | 2026-08-07 | 2026-08-11 | Ray Swan / Codex | Replaced the legacy Bicep/Databricks sequence with the R1 Terraform Azure ML batch acceptance sequence. |
| 0.2.0 | 2026-08-07 | 2026-08-07 | Ray Swan / Codex | Documented environment-specific Key Vault purge-protection behavior. |
| 0.1.0 | 2026-08-07 | 2026-08-07 | Ray Swan / Codex | Initial deployment guide. |
