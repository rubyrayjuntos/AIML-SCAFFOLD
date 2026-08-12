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

Recommended GitHub Environment names are `dev`, `test`, and `prod`. Production should require environment approval before deployment and model promotion.

Protected-branch policy controls eligible deployment refs; it is not an independent human approval. If native required reviewers are unavailable, use the ADR 0008 digest-bound manual dispatch contract and report independent reviewer separation as unavailable when only one human operates the repository.

## Key Vault

Generated R1 Terraform creates an RBAC-enabled project Key Vault inside the assigned environment resource group. Runtime managed identities receive only required access. The deployment identity receives scoped infrastructure permissions and only the evidence-container data role required by generated workflows.

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
| 0.4.0 | 2026-08-07 | 2026-08-12 | Ray Swan / Codex | Distinguished protected branches from manual approval and referenced the digest-bound fallback contract. |
| 1.0.0-rc1 | 2026-08-07 | 2026-08-11 | Ray Swan / Codex | Aligned identity, Key Vault, environment profiles, and setup with the R1 Terraform factory. |
| 0.1.0 | 2026-08-07 | 2026-08-07 | Ray Swan / Codex | Initial reusable identity, Key Vault, and environment-profile guidance. |
