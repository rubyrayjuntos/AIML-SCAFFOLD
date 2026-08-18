data "azurerm_resource_group" "backend" {
  name = var.backend_resource_group_name
}

data "azurerm_storage_account" "backend" {
  name                = var.backend_storage_account_name
  resource_group_name = data.azurerm_resource_group.backend.name
}

resource "azurerm_resource_group" "environment" {
  name     = var.environment_resource_group_name
  location = var.location

  tags = {
    product     = var.product_name
    environment = "dev"
    owner       = var.product_owner
    cost_center = var.cost_center
    managed_by  = "r1-bootstrap-terraform"
  }

  lifecycle {
    prevent_destroy = true
  }
}

resource "azurerm_storage_container" "state" {
  name                  = var.backend_container_name
  storage_account_id    = data.azurerm_storage_account.backend.id
  container_access_type = "private"

  lifecycle {
    prevent_destroy = true
  }
}

# ADR 0012: infra/platform_foundation/ gets its own dedicated state container in
# this same shared backend account, independently plannable from the R1 bootstrap
# state above - not a resource either root co-manages.
resource "azurerm_storage_container" "platform_foundation_state" {
  name                  = var.platform_foundation_container_name
  storage_account_id    = data.azurerm_storage_account.backend.id
  container_access_type = "private"

  lifecycle {
    prevent_destroy = true
  }
}

locals {
  contributor_role_id                   = "/subscriptions/${var.subscription_id}/providers/Microsoft.Authorization/roleDefinitions/b24988ac-6180-42a0-ab88-20f7382dd24c"
  user_access_administrator_role_id     = "/subscriptions/${var.subscription_id}/providers/Microsoft.Authorization/roleDefinitions/18d7d88d-d35e-4fb5-a5c3-7773c20a72d9"
  storage_blob_data_contributor_role_id = "/subscriptions/${var.subscription_id}/providers/Microsoft.Authorization/roleDefinitions/ba92f5b4-2d11-453d-a403-e96b0029c9fe"
}

resource "azurerm_role_assignment" "backend_data" {
  name                             = uuidv5("url", "${azurerm_storage_container.state.id}|${var.deployment_principal_object_id}|${local.storage_blob_data_contributor_role_id}")
  scope                            = azurerm_storage_container.state.id
  role_definition_id               = local.storage_blob_data_contributor_role_id
  principal_id                     = var.deployment_principal_object_id
  principal_type                   = "ServicePrincipal"
  skip_service_principal_aad_check = true
}

# ADR 0012 / ADR 0014: granted to the factory's OWN identity, not
# deployment_principal_object_id above. Originally granted to the shared R1
# identity, then corrected per ADR 0014 once that was found to let the
# generated project's OIDC credential inherit platform-foundation access
# through the same underlying service principal.
resource "azurerm_role_assignment" "platform_foundation_backend_data" {
  name                             = uuidv5("url", "${azurerm_storage_container.platform_foundation_state.id}|${var.platform_foundation_principal_object_id}|${local.storage_blob_data_contributor_role_id}")
  scope                            = azurerm_storage_container.platform_foundation_state.id
  role_definition_id               = local.storage_blob_data_contributor_role_id
  principal_id                     = var.platform_foundation_principal_object_id
  principal_type                   = "ServicePrincipal"
  skip_service_principal_aad_check = true
}

resource "azurerm_role_assignment" "environment_contributor" {
  name                             = uuidv5("url", "${azurerm_resource_group.environment.id}|${var.deployment_principal_object_id}|${local.contributor_role_id}")
  scope                            = azurerm_resource_group.environment.id
  role_definition_id               = local.contributor_role_id
  principal_id                     = var.deployment_principal_object_id
  principal_type                   = "ServicePrincipal"
  skip_service_principal_aad_check = true
}

resource "azurerm_role_assignment" "environment_user_access_administrator" {
  name                             = uuidv5("url", "${azurerm_resource_group.environment.id}|${var.deployment_principal_object_id}|${local.user_access_administrator_role_id}")
  scope                            = azurerm_resource_group.environment.id
  role_definition_id               = local.user_access_administrator_role_id
  principal_id                     = var.deployment_principal_object_id
  principal_type                   = "ServicePrincipal"
  skip_service_principal_aad_check = true
}
