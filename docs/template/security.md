# Template security

## Identity

GitHub Actions uses Entra federated credentials and OIDC. Runtime services use managed identities. Personal access tokens and long-lived client secrets are not supported in production.

## Resource boundaries

The template distinguishes shared enterprise resources from project-owned resources. Project identities receive only the roles required for their environment and scenario.

## Network profiles

Production uses private connectivity, private endpoints, private DNS, and disabled public access where supported. Development may use public endpoints only through an explicit lower-cost profile documented as a tradeoff.

## Data and agent controls

Foundry tools are allowlisted, read-only application functions. Agents cannot issue arbitrary SQL, access unapproved tables, or mutate data. Logs must exclude secrets and access tokens.

## Documentation changelog

| Version | Created | Modified | Who | Notes |
|---|---|---|---|---|
| 0.1.0 | 2026-08-07 | 2026-08-07 | Ray Swan / Codex | Initial template security policy. |
