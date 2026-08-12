# Identity, Key Vault, and environment profiles

## Design principle

Local development and CI/CD use different authentication paths, but both target the same parameterized environment profiles. No credentials are committed to the repository.

## Local Azure login

```bash
az login --tenant "$AZURE_TENANT_ID"
az account set --subscription "$AZURE_SUBSCRIPTION_ID"
export AZURE_RESOURCE_GROUP=rg-aiml-scaffold-dev
./scripts/validate-azure-context.sh dev
```

The local developer identity should have only the roles needed for development. It is not reused as the production deployment identity.

## GitHub Actions OIDC

Create one Entra application/service principal for the repository deployment workflow, then add federated credentials for the approved GitHub repository and environments. Grant the service principal least-privilege access at the environment resource-group scope.

The workflow uses `azure/login@v2` with:

- `AZURE_CLIENT_ID`;
- `AZURE_TENANT_ID`;
- `AZURE_SUBSCRIPTION_ID`.

These are identifiers, not secrets. The workflow receives a short-lived token through OIDC; no client secret is stored in GitHub.

Terraform plan and apply workflows also set `ARM_USE_OIDC=true`, `ARM_USE_AZUREAD=true`, and the corresponding `ARM_CLIENT_ID`, `ARM_TENANT_ID`, and `ARM_SUBSCRIPTION_ID` values. This binds both the AzureRM backend and provider to workload-identity federation instead of the Azure CLI user authentication path.

Recommended GitHub Environment names are `dev`, `test`, and `prod`. Production should require environment approval before deployment and model promotion.

Protected-branch policy controls eligible deployment refs; it is not an independent human approval. If native required reviewers are unavailable, use the ADR 0008 digest-bound manual dispatch contract and report independent reviewer separation as unavailable when only one human operates the repository.

## Key Vault

Generated R1 Terraform creates an RBAC-enabled project Key Vault inside the assigned environment resource group. The Azure ML workspace keeps its recommended system-assigned identity and explicitly uses identity-based access for its default storage. Azure ML owns the workspace identity's service-created Azure AI Administrator assignment; workload Terraform owns the data-plane assignments described below.

| Principal source | Role | Scope | Purpose | Creation owner | Dependency | Live proof | Removal condition |
|---|---|---|---|---|---|---|---|
| Workspace system-assigned identity | Azure AI Administrator | Environment resource group | Azure ML access to associated Storage, Key Vault, Application Insights, and any service-created ACR | Azure ML service | Workspace creation | Verify exact principal and assignment after apply, then exercise workspace creation and associated-resource access | Workspace deletion |
| Project-created compute UAMI | Storage Blob Data Contributor | Project storage account | Model/job input and output, MLflow, and registry operations with Shared Key disabled | Workload Terraform | UAMI and storage before compute clusters | Training output plus conditional model registration | No generated job, MLflow, or registry path uses the identity |
| GitHub OIDC deployment principal | Storage Blob Data Contributor | Project storage account | Local-source upload, model registration, batch workflow input/output, and evidence publication | Workload Terraform | Storage before lifecycle workflows | Training submission, registration, batch invocation, and evidence write | All workflow data operations move to a narrower runtime identity |

The compute UAMI is project-owned. Its resource and scope are known in the plan, while its principal ID is expected to be known only after apply. Terraform references that principal directly, skips the initial Entra replication check, and makes compute creation depend on the storage role assignment. Arbitrary externally supplied runtime principal IDs are prohibited. Post-apply principal and role verification is mandatory.

R1 creates no ACR because the selected Azure ML path does not require a project-managed registry. Key Vault and Application Insights need no additional Terraform-created data-plane assignment for the current non-CMK, non-secret-injection batch scope. Any future operation that proves otherwise must add a purpose-specific role and live proof rather than broadening permissions speculatively.

Authoritative basis, reviewed 2026-08-12:

- [Disable Shared Key access for Azure ML workspace storage](https://learn.microsoft.com/azure/machine-learning/how-to-disable-local-auth-storage?view=azureml-api-2) requires identity-based system datastores and identifies a compute UAMI with Storage Blob Data Contributor for model and MLflow input/output.
- [Azure ML service authentication](https://learn.microsoft.com/azure/machine-learning/how-to-identity-based-service-authentication?view=azureml-api-2) recommends a system-assigned workspace identity for associated resources and documents minimum compute/storage roles.
- [Azure ML workspace roles](https://learn.microsoft.com/azure/machine-learning/how-to-assign-roles?view=azureml-api-2) documents the Azure AI Administrator assignment used for new workspace system identities.

Store values such as Databricks OAuth credentials, Foundry configuration secrets, and application connection details in Key Vault. Reference them from Container Apps or deployment configuration through secret references. Never put values in `.env`, YAML profiles, workspace files, or GitHub logs.

## Environment profiles

Generated profiles under `config/` contain non-secret environment identity:

- resource group;
- location;
- network posture;
- Key Vault name;
- Azure ML workspace and evidence configuration.

They are intentionally declarative and safe to review. Secrets and subscription-specific deployment credentials are supplied by the local shell or GitHub Environment.

## Repeatable setup sequence

1. Select `dev`, `test`, or `prod`.
2. Load the corresponding non-secret profile.
3. Authenticate locally with `az login` or in CI with OIDC.
4. Run `scripts/validate-azure-context.sh`.
5. Run `aiml-scaffold doctor` for read-only prerequisite checks.
6. Run and review the generated Terraform plan.
7. Apply Dev infrastructure only after separate approval.
8. Run the generated Azure ML batch lifecycle workflows.

## Documentation changelog

| Version | Created | Modified | Who | Notes |
|---|---|---|---|---|
| 0.6.0 | 2026-08-07 | 2026-08-12 | Ray Swan / Codex | Selected project-owned AML identities, explicit identity-based storage, purpose-scoped roles, dependency ordering, and mandatory post-apply verification. |
| 0.5.0 | 2026-08-07 | 2026-08-12 | Ray Swan / Codex | Documented the AzureRM OIDC environment contract required after `azure/login` for Terraform backend and provider authentication. |
| 0.4.0 | 2026-08-07 | 2026-08-12 | Ray Swan / Codex | Distinguished protected branches from manual approval and referenced the digest-bound fallback contract. |
| 1.0.0-rc1 | 2026-08-07 | 2026-08-11 | Ray Swan / Codex | Aligned identity, Key Vault, environment profiles, and setup with the R1 Terraform factory. |
| 0.1.0 | 2026-08-07 | 2026-08-07 | Ray Swan / Codex | Initial reusable identity, Key Vault, and environment-profile guidance. |
