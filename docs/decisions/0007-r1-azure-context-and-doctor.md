# ADR 0007: Azure context and read-only preflight are explicit R1 contracts

## Decision

An R1 manifest declares the expected Azure tenant and deployment subscription independently from the Terraform backend. Backend resource IDs must contain UUID subscription IDs and share one backend subscription. A backend in another subscription is rejected unless `policy.allow_cross_subscription_backend` is explicitly true.

The resolved plan records the expected tenant, deployment subscription, backend subscription, cross-subscription decision, deployment identity client/object ID configuration references, and intended GitHub federated credential issuer, subject, and audience. These normalized fields participate in resolved-plan and generation identity.

Authenticated `doctor` is read-only and reports each boundary independently using `passed`, `failed`, `warning`, `not_exercised`, or `not_applicable`. It checks active Azure context, active versus intended identity, environment resource group, backend management-plane visibility, container existence, Entra data-plane read access, shared-key posture, application/principal linkage, federated credential configuration, exact environment-scoped RBAC, prohibited subscription Owner, compute SKU availability, and point-in-time quota sufficiency.

Doctor does not write Terraform state, acquire a state lock, exchange a GitHub OIDC token, plan or apply infrastructure, submit Azure ML jobs, or mutate Azure resources. Those results remain `not_exercised`. In particular, a successful local authenticated check proves the active CLI identity's visibility and authorization; only a GitHub workflow proves token exchange as the intended deployment identity.

## Consequences

- A platform backend may be centralized in another subscription, but only through explicit policy.
- Backend placement cannot silently determine the project deployment subscription.
- A mismatched local identity is visible as a warning rather than being collapsed into OIDC readiness.
- Point-in-time SKU and quota results are preflight evidence, not durable capacity guarantees.
- Terraform planning and all Azure mutation remain separately approval-gated.

## Documentation changelog

| Version | Created | Modified | Who | Notes |
|---|---|---|---|---|
| 0.1.0 | 2026-08-11 | 2026-08-11 | Ray Swan / Codex | Established explicit tenant, deployment/backend subscription, identity intent, cross-subscription policy, and tri-state read-only doctor boundaries. |
