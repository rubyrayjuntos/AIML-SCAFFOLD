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
