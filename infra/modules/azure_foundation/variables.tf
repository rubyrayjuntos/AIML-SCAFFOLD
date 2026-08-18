variable "subscription_id" {
  type = string
}

variable "location" {
  type = string
}

variable "product_name" {
  type = string
}

variable "product_owner" {
  type = string
}

variable "cost_center" {
  type = string
}

variable "environment_resource_group_name" {
  type = string
}

variable "backend_resource_group_name" {
  type = string
}

variable "backend_storage_account_name" {
  type = string
}

variable "backend_container_name" {
  type = string
}

variable "platform_foundation_container_name" {
  description = "Dedicated state container for the R3.2 platform-foundation Terraform root (Databricks/Foundry), independent of the R1 bootstrap container."
  type        = string
}

variable "deployment_principal_object_id" {
  description = "R1/generated-project deployment identity. Grants scoped to this identity's own bootstrap concerns only - see ADR 0014."
  type        = string
}

variable "platform_foundation_principal_object_id" {
  description = "Factory's own deployment identity (ADR 0014). Used only for the platform_foundation state container grant - deliberately not deployment_principal_object_id, to avoid re-creating the identity-sharing problem ADR 0014 corrects."
  type        = string
}
