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
  type = string
}
