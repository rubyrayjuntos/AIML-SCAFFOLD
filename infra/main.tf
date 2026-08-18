module "entra_identity" {
  source = "./modules/entra_identity"

  application_display_name    = var.entra_application_display_name
  application_owner_object_id = var.application_owner_object_id
  federated_credential_name   = var.federated_credential_name
  federated_subject           = var.federated_subject
}

module "github_prerequisites" {
  source = "./modules/github_prerequisites"

  repository_name        = var.github_repository
  repository_visibility  = var.github_repository_visibility
  environment_name       = var.github_environment
  azure_client_id        = module.entra_identity.application_client_id
  azure_client_object_id = module.entra_identity.service_principal_object_id
  azure_tenant_id        = var.tenant_id
  azure_subscription_id  = var.subscription_id
}

module "azure_foundation" {
  source = "./modules/azure_foundation"

  subscription_id                         = var.subscription_id
  location                                = var.location
  product_name                            = var.product_name
  product_owner                           = var.product_owner
  cost_center                             = var.cost_center
  environment_resource_group_name         = var.environment_resource_group_name
  backend_resource_group_name             = var.backend_resource_group_name
  backend_storage_account_name            = var.backend_storage_account_name
  backend_container_name                  = var.backend_container_name
  platform_foundation_container_name      = var.platform_foundation_container_name
  deployment_principal_object_id          = module.entra_identity.service_principal_object_id
  platform_foundation_principal_object_id = module.factory_identity.service_principal_object_id
}

# ADR 0014: the factory's own CI/CD identity, separate from the R1/generated-
# project identity above. Neither is a superset of the other - see the ADR for
# why sharing one principal across both contexts was rejected.
module "factory_identity" {
  source = "./modules/entra_identity"

  application_display_name    = "gh-aiml-scaffold-platform-oidc"
  application_owner_object_id = var.application_owner_object_id
  federated_credential_name   = "github-aiml-scaffold-platform-dev-environment"
  federated_subject           = "repo:${var.factory_github_owner}@${var.factory_github_owner_id}/${var.factory_github_repository}@${var.factory_github_repository_id}:environment:dev"
}

# Prod federated credential on the SAME factory app (scaffolded, not exercised
# in R3.2 - no prod Databricks/Foundry workload exists yet to apply against).
resource "azuread_application_federated_identity_credential" "factory_identity_prod" {
  application_id = module.factory_identity.application_id
  display_name   = "github-aiml-scaffold-platform-prod-environment"
  description    = "GitHub protected Prod environment for the AIML-SCAFFOLD platform foundation (scaffolded, not yet exercised)."
  audiences      = ["api://AzureADTokenExchange"]
  issuer         = "https://token.actions.githubusercontent.com"
  subject        = "repo:${var.factory_github_owner}@${var.factory_github_owner_id}/${var.factory_github_repository}@${var.factory_github_repository_id}:environment:prod"
}

locals {
  factory_environment_variables = {
    AZURE_CLIENT_ID         = module.factory_identity.application_client_id
    AZURE_TENANT_ID         = var.tenant_id
    AZURE_SUBSCRIPTION_ID   = var.subscription_id
    APPLY_AUTHORIZED_ACTORS = var.factory_github_owner
  }
}

module "factory_github_environment_dev" {
  source = "./modules/factory_github_environment"

  repository_name  = var.factory_github_repository
  environment_name = "dev"
  variables        = local.factory_environment_variables
}

module "factory_github_environment_prod" {
  source = "./modules/factory_github_environment"

  repository_name  = var.factory_github_repository
  environment_name = "prod"
  variables        = local.factory_environment_variables
}
