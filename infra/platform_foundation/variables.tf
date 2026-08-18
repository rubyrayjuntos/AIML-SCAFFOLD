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

# R3.2 Step D: both identities already exist and already do other jobs (R1's
# deployment/OIDC identity, R1's compute identity). The grants declared against
# them here are a genuine expansion of responsibility onto pre-existing,
# already-audited identities - not a fresh, unreviewed identity with unknown
# blast radius. RBAC assignment succeeding is not evidence either identity can
# actually use it - that live proof is R3.3's job, not declared here.

variable "apply_principal_object_id" {
  description = "Object ID of the existing gh-azure-ai-ml-ops-r1-dev-oidc service principal (R1's GitHub OIDC deployment identity), gaining management-plane grants on platform_foundation resources."
  type        = string
}

variable "compute_principal_object_id" {
  description = "Object ID of the existing id-azure-ai-ml-ops-dev-compute user-assigned identity (R1's Azure ML compute identity), gaining data-plane (runtime/consumer) grants on platform_foundation resources."
  type        = string
}
