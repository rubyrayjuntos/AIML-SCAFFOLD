variable "tenant_id" {
  description = "Microsoft Entra tenant for the R1 Dev deployment identity."
  type        = string
}

variable "subscription_id" {
  description = "Azure subscription for bootstrap and generated R1 Dev resources."
  type        = string
}

variable "location" {
  description = "Azure region for the Dev resource group."
  type        = string
  default     = "eastus"
}

variable "product_name" {
  description = "Normalized product slug."
  type        = string
  default     = "azure-ai-ml-ops"
}

variable "product_owner" {
  description = "Product owner recorded in tags and the replacement manifest."
  type        = string
  default     = "Ray Swan"
}

variable "cost_center" {
  description = "Permitted sentinel when no organizational cost center exists."
  type        = string
  default     = "UNASSIGNED"
}

variable "github_owner" {
  description = "GitHub repository owner."
  type        = string
  default     = "rubyrayjuntos"
}

variable "github_repository" {
  description = "Generated deployment repository name."
  type        = string
  default     = "azure-aiml-ops"
}

variable "github_environment" {
  description = "Protected GitHub deployment environment."
  type        = string
  default     = "dev"
}

variable "github_repository_visibility" {
  description = "Visibility of the generated deployment repository."
  type        = string
  default     = "public"

  validation {
    condition     = contains(["public", "private"], var.github_repository_visibility)
    error_message = "GitHub repository visibility must be public or private."
  }
}

variable "backend_resource_group_name" {
  description = "Existing shared Terraform backend resource group."
  type        = string
  default     = "rg-azmlops-0001dev-tf"
}

variable "backend_storage_account_name" {
  description = "Existing shared Terraform backend storage account."
  type        = string
  default     = "stazmlops0001devtf"
}

variable "backend_container_name" {
  description = "Dedicated R1 backend container."
  type        = string
  default     = "azure-ai-ml-ops-r1"
}

variable "environment_resource_group_name" {
  description = "Administrator-owned R1 Dev environment boundary."
  type        = string
  default     = "rg-azure-ai-ml-ops-dev"
}

variable "entra_application_display_name" {
  description = "Single-tenant GitHub deployment application display name."
  type        = string
  default     = "gh-azure-ai-ml-ops-r1-dev-oidc"
}

variable "federated_credential_name" {
  description = "Stable federated identity credential name."
  type        = string
  default     = "github-azure-aiml-ops-dev-environment"
}

variable "federated_subject" {
  description = "Exact GitHub Actions OIDC subject."
  type        = string
  default     = "repo:rubyrayjuntos@204968804/azure-aiml-ops@1331566719:environment:dev"
}

variable "application_owner_object_id" {
  description = "Entra object ID retained as an owner of the new application."
  type        = string
  default     = "a703a773-2881-456b-a8fc-3a007d6c2463"
}
