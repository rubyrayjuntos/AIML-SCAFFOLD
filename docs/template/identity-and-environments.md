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

## Key Vault

The Bicep deployment creates or consumes an RBAC-enabled Key Vault. Runtime managed identities receive only the required secret-read role. CI identities receive deployment permissions but should not automatically receive application data access.

Store values such as Databricks OAuth credentials, Foundry configuration secrets, and application connection details in Key Vault. Reference them from Container Apps or deployment configuration through secret references. Never put values in `.env`, YAML profiles, workspace files, or GitHub logs.

## Environment profiles

Profiles under `config/environments/` contain non-secret environment identity:

- resource group;
- location;
- catalog;
- network posture;
- Key Vault name;
- Databricks target;
- Foundry project name.

They are intentionally declarative and safe to review. Secrets and subscription-specific deployment credentials are supplied by the local shell or GitHub Environment.

## Repeatable setup sequence

1. Select `dev`, `test`, or `prod`.
2. Load the corresponding non-secret profile.
3. Authenticate locally with `az login` or in CI with OIDC.
4. Run `scripts/validate-azure-context.sh`.
5. Run Bicep `what-if`.
6. Deploy infrastructure only after review/approval.
7. Deploy the Databricks Bundle and scenario workflow.

## Documentation changelog

| Version | Created | Modified | Who | Notes |
|---|---|---|---|---|
| 0.1.0 | 2026-08-07 | 2026-08-07 | Ray Swan / Codex | Initial reusable identity, Key Vault, and environment-profile guidance. |
