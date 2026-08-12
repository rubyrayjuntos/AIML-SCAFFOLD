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

  subscription_id                 = var.subscription_id
  location                        = var.location
  product_name                    = var.product_name
  product_owner                   = var.product_owner
  cost_center                     = var.cost_center
  environment_resource_group_name = var.environment_resource_group_name
  backend_resource_group_name     = var.backend_resource_group_name
  backend_storage_account_name    = var.backend_storage_account_name
  backend_container_name          = var.backend_container_name
  deployment_principal_object_id  = module.entra_identity.service_principal_object_id
}
