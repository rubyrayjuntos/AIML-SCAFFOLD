# R1 Dev bootstrap deployment runbook

This runbook provisions only the approved prerequisites for the `azure-ai-ml-ops` R1 Dev candidate. It does not generate or deploy the Azure ML project. For that — the actual Azure ML workspace, storage, compute, and workload lifecycle deployment that follows this bootstrap, plus its live status log — see [`r1-deployment-plan.md`](r1-deployment-plan.md).

## Approved scope

- Maintain public GitHub repository `rubyrayjuntos/azure-aiml-ops` and environment `dev` with protected-branch deployment policy.
- Create resource group `rg-azure-ai-ml-ops-dev` in East US.
- Create private container `azure-ai-ml-ops-r1` in existing storage account `stazmlops0001devtf`.
- Create one single-tenant Entra application/service principal with no secret.
- Create the exact ID-qualified subject `repo:rubyrayjuntos@204968804/azure-aiml-ops@1331566719:environment:dev`.
- Assign container-scoped `Storage Blob Data Contributor` and Dev-resource-group-scoped `Contributor` plus `User Access Administrator`.
- Populate the protected GitHub environment with Azure client/object, tenant, and subscription identifiers. These are identifiers, not credentials.

No subscription Owner role, client secret, legacy identity reuse, legacy state-container reuse, Azure ML resource, Terraform workload plan, or Test/Prod mutation is included.

The current GitHub billing plan does not support required-reviewer protection for a private repository. The first apply proved that limitation with an HTTP 422 response. Bootstrap therefore creates the environment with protected-branch policy only. The manifest's `dev_manual` approval posture is not yet enforced and remains a release stop condition until the repository plan supports reviewers or an equivalent external approval control is approved.

The repository is intentionally empty because generated-source publication was not part of this bootstrap approval. Consequently, it has no default or protected branch yet. After the separately approved initial source push, branch protection must be configured before a `dev` environment workflow can satisfy the protected-branch deployment policy.

## Bootstrap-state sequence

The target state container does not exist before bootstrap. After explicit deployment-risk acknowledgement:

1. Reverify the active tenant, subscription, Azure user, GitHub user, and absence of all create targets.
2. Create only the private `azure-ai-ml-ops-r1` container through the Azure management plane.
3. Initialize `infra/` against `backend-dev.hcl` using Entra authentication.
4. Import the container into `module.azure_foundation.azurerm_storage_container.state` before planning.
5. Save and review the Terraform plan. Confirm no update or deletion of existing resources and no Owner assignment.
6. Stop for explicit apply approval unless the immediately preceding user authorization explicitly covers the reviewed plan.
7. Apply the saved plan, verify outputs independently, run authenticated doctor, and retain receipts.

If initialization or import fails, retain the empty private container and stop. Do not delete existing state or use account keys. If apply partially succeeds, preserve Terraform state and correct it through a reviewed follow-up plan.

## Local validation

```bash
terraform -chdir=infra fmt -check -recursive
terraform -chdir=infra init -backend=false -lockfile=readonly
terraform -chdir=infra validate
```

The initial deployment completed on 2026-08-11. On 2026-08-12, an approved corrective plan updated only the Entra federated credential from the conventional repository subject to GitHub's exact ID-qualified subject. The saved plan contained `0` adds, `1` in-place update, and `0` destroys; direct Entra verification passed and the post-apply remote plan returned detailed exit code `0`. This proves bootstrap convergence only; OIDC token exchange requires a GitHub Actions run and Azure ML workload behavior remains unexercised.

## Documentation changelog

| Version | Created | Modified | Who | Notes |
|---|---|---|---|---|
| 0.4.0 | 2026-08-11 | 2026-08-17 | Ray Swan / Claude | Added a cross-link to `r1-deployment-plan.md`, the complementary workload deployment plan and status log that follows this bootstrap runbook. |
| 0.3.0 | 2026-08-11 | 2026-08-12 | Ray Swan / Codex | Recorded the identity-only correction to GitHub's ID-qualified subject, adopted the owner-approved public repository intent, and verified a clean post-apply plan. |
| 0.2.0 | 2026-08-11 | 2026-08-11 | Ray Swan / Codex | Recorded the GitHub private-repository billing limitation, supported protected-branch fallback, and unresolved manual-approval enforcement gate. |
| 0.1.0 | 2026-08-11 | 2026-08-11 | Ray Swan / Codex | Defined approved Terraform bootstrap scope, circular-backend seed/import sequence, risk gates, rollback, and validation boundary. |
