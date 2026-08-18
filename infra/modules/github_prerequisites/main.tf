resource "github_repository" "generated" {
  name                   = var.repository_name
  description            = "Generated Azure AI ML Ops R1 Dev project repository."
  visibility             = var.repository_visibility
  has_issues             = true
  has_projects           = false
  has_wiki               = false
  has_discussions        = false
  auto_init              = false
  delete_branch_on_merge = true
  archive_on_destroy     = true

  lifecycle {
    prevent_destroy = true
  }
}

resource "github_repository_environment" "dev" {
  repository  = github_repository.generated.name
  environment = var.environment_name

  deployment_branch_policy {
    protected_branches     = true
    custom_branch_policies = false
  }
}

locals {
  environment_values = {
    AZURE_CLIENT_ID        = var.azure_client_id
    AZURE_CLIENT_OBJECT_ID = var.azure_client_object_id
    AZURE_TENANT_ID        = var.azure_tenant_id
    AZURE_SUBSCRIPTION_ID  = var.azure_subscription_id
  }
}

resource "github_actions_environment_secret" "azure_context" {
  for_each = local.environment_values

  repository  = github_repository.generated.name
  environment = github_repository_environment.dev.environment
  secret_name = each.key
  value       = each.value
}
