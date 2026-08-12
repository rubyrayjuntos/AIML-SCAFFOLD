# Template deployment

## Ownership

Terraform is the authoritative generated Azure deployment path for R1. Existing Bicep is an experimental reference and must never manage an R1 Terraform resource group or any Terraform-owned resource.

The generated repository consumes an administrator-created resource group, remote Terraform backend, OIDC identity, and scoped grants. The generated deployment identity does not require subscription-level Owner. Databricks deployment is outside R1.

## Deployment sequence

1. Validate and resolve the manifest without cloud operations.
2. Generate into an empty directory and verify the generation receipt.
3. Run `aiml-scaffold doctor` in offline mode, then authenticated read-only mode.
4. Authenticate GitHub Actions with Entra OIDC.
5. Run and review the Dev Terraform plan and its complete six-file schema `1.0` review artifact.
6. Apply Terraform only through the separate digest-bound manual workflow using the reviewed plan artifact. The apply workflow must never replan.
7. Run Azure ML training, evaluation, and conditional registration.
8. Deploy an explicit registered model version to the batch endpoint.
9. Invoke the endpoint and independently verify evidence and outputs.
10. Regenerate without source edits and require a clean second Terraform plan.

## Enterprise integration

The R1 manifest references centrally administered Terraform state and identity prerequisites. Each environment owns an independent Azure ML workspace, storage boundary, evidence container, and Terraform state key.

No R1 CLI command deploys or destroys resources. Failure rollback preserves Terraform state and evidence. Any corrective apply or disposable-environment destroy requires a reviewed plan and explicit approval.

When native GitHub required reviewers are unavailable, R1 uses `manual_dispatch_with_plan_digest`: the plan workflow publishes the binary plan, its structurally sanitized JSON representation, dual digests, approval metadata, and a versioned artifact manifest. Apply requires the exact reviewed digest, source commit, generation identity, target environment, backend/state identity, consistent action summary, and confirmation phrase. This is deliberate manual authorization, but it does not claim independent separation of duties when one person is the only operator.

## Documentation changelog

| Version | Created | Modified | Who | Notes |
|---|---|---|---|---|
| 0.4.0 | 2026-08-07 | 2026-08-12 | Ray Swan / Codex | Required the schema 1.0 six-file saved-plan artifact and apply-side provenance, backend, digest, and action verification. |
| 0.3.0 | 2026-08-07 | 2026-08-12 | Ray Swan / Codex | Defined digest-bound manual plan/apply authorization without replanning or an unsupported independent-reviewer claim. |
| 1.0.0-rc1 | 2026-08-07 | 2026-08-11 | Ray Swan / Codex | Replaced the legacy Bicep/Databricks sequence with the R1 Terraform Azure ML batch acceptance sequence. |
| 0.2.0 | 2026-08-07 | 2026-08-07 | Ray Swan / Codex | Documented environment-specific Key Vault purge-protection behavior. |
| 0.1.0 | 2026-08-07 | 2026-08-07 | Ray Swan / Codex | Initial deployment guide. |
