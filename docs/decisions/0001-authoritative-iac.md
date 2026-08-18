# ADR 0001: Terraform is authoritative for the R1 Azure ML factory

## Decision

Terraform is the only supported generated Azure infrastructure path for the R1 Azure ML batch factory. This preserves the infrastructure route already exercised by the Azure ML reference implementation while the manifest, contracts, and generator are introduced.

Bicep remains in this repository as an experimental Azure-native reference. R1 does not generate, deploy, or claim conformance for Bicep. A resource or environment has exactly one IaC owner: Bicep must never target a Terraform-owned resource group, state, or resource.

Changing the supported provider requires the candidate to pass the same provider-conformance and clean-room acceptance suite as Terraform.

## Consequences

- Generated projects declare `infrastructure.azure.provider: terraform`.
- The deployment workflow uses Terraform plan review before apply.
- Existing Bicep validation remains useful static evidence, but is not R1 release evidence.
- Terraform state backends and environment resource groups are bootstrap prerequisites supplied by platform administration.

## Documentation changelog

| Version | Created | Modified | Who | Notes |
|---|---|---|---|---|
| 0.2.0 | 2026-08-07 | 2026-08-11 | Ray Swan / Codex | Superseded the original decision for R1: Terraform is the supported Azure ML generator output and Bicep is experimental. |
| 0.1.0 | 2026-08-07 | 2026-08-07 | Ray Swan / Codex | Initial infrastructure-as-code ownership decision. |
