variable "tenant_id" {
  description = "Microsoft Entra tenant for the primary subscription."
  type        = string
}

variable "subscription_id" {
  description = "Primary Azure subscription hosting the shared AI platform foundation."
  type        = string
}

variable "location" {
  description = "Azure region for platform_foundation resources (Databricks). Note: the adopted Foundry resource is in eastus2, imported as-is - see ADR 0012 and the R3.2 plan."
  type        = string
  default     = "eastus"
}

# R3.2 Step D: RBAC assignment succeeding is not evidence either identity can
# actually use it - that live proof is R3.3's job, not declared here.
#
# ADR 0014 correction: apply_principal_object_id originally pointed at the
# shared R1 deployment identity (gh-azure-ai-ml-ops-r1-dev-oidc). That identity
# is also federated to the generated project's own OIDC credential, so granting
# it platform-foundation RBAC would have let the generated project inherit
# factory-administration access through the same underlying principal.
# Corrected to point at gh-aiml-scaffold-platform-oidc, the factory-specific
# identity ADR 0014 introduces - a genuinely separate identity, not a second
# federated credential on the same one.

variable "apply_principal_object_id" {
  description = "Object ID of the gh-aiml-scaffold-platform-oidc service principal (the factory's own GitHub OIDC deployment identity, ADR 0014), gaining management-plane grants on platform_foundation resources."
  type        = string
}

variable "compute_principal_object_id" {
  description = "Object ID of the existing id-azure-ai-ml-ops-dev-compute user-assigned identity (R1's Azure ML compute identity), gaining data-plane (runtime/consumer) grants on platform_foundation resources."
  type        = string
}
