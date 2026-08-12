# Template security

## Identity

GitHub Actions uses Entra federated credentials and OIDC. Runtime services use managed identities. Personal access tokens and long-lived client secrets are not supported in production.

## Resource boundaries

The template distinguishes administrator-provided bootstrap resources from Terraform-owned project resources. The workspace system identity, project-created compute identity, and GitHub workflow identity have separate ownership and purposes. Storage uses identity-based authorization with Shared Key disabled. Data-plane roles are scoped to the project storage account only where the current training, registry, batch, or evidence operation requires them. Subscription-level Owner is prohibited.

## Network profiles

R1 live acceptance is Dev-only. The resolved plan and documentation must expose any public-network or always-on-resource tradeoff. Production private-network conformance is deferred and must not inherit a Dev evidence claim.

## Data and agent controls

Foundry is outside R1. Generated evidence rejects sensitive metadata keys recursively and permits only identifiers, metrics, hashes, and immutable artifact references. Credentials, tokens, raw training data, prompts, and sensitive inference payloads are prohibited.

## Documentation changelog

| Version | Created | Modified | Who | Notes |
|---|---|---|---|---|
| 1.0.0-rc2 | 2026-08-07 | 2026-08-12 | Ray Swan / Codex | Documented identity-based workspace storage and separated workspace, compute, and workflow identity permissions. |
| 1.0.0-rc1 | 2026-08-07 | 2026-08-11 | Ray Swan / Codex | Added R1 scoped identity, Dev network boundary, and evidence redaction controls. |
| 0.1.0 | 2026-08-07 | 2026-08-07 | Ray Swan / Codex | Initial template security policy. |
