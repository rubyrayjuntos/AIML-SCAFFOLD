# Template deployment

## Ownership

Bicep is the supported Azure deployment path. Terraform is a separately validated portability path and must never manage the same resource group or resources as Bicep.

Databricks code, workflows, permissions, and environment targets are deployed with Databricks Asset Bundles.

## Deployment sequence

1. Select the environment profile.
2. Authenticate GitHub Actions with Entra OIDC.
3. Run Bicep `what-if`.
4. Deploy or update the environment resource group.
5. Configure/validate Unity Catalog and workspace permissions.
6. Validate and deploy the Databricks Bundle.
7. Run data-quality and training workflows.
8. Register and validate the candidate model.
9. Obtain production approval.
10. Promote the model alias and update serving.
11. Run API, serving, and Foundry smoke tests.

## Enterprise integration

Production may consume centrally governed networking, Log Analytics, Key Vault, Databricks metastore, and identity resources. The template must accept those resource IDs rather than recreate shared enterprise resources.

The Key Vault template property `enablePurgeProtection` is omitted for `dev` and `test` because Azure rejects an explicit `false` value; it is enabled for `prod` and is irreversible once set.

## Documentation changelog

| Version | Created | Modified | Who | Notes |
|---|---|---|---|---|
| 0.2.0 | 2026-08-07 | 2026-08-07 | Ray Swan / Codex | Documented environment-specific Key Vault purge-protection behavior. |
| 0.1.0 | 2026-08-07 | 2026-08-07 | Ray Swan / Codex | Initial deployment guide. |
