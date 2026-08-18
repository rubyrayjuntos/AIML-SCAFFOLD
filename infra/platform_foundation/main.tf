# R3.2 Step B (see docs/superpowers/plans/r3.2-platform-foundation.md and
# ADR 0012). This is a saved-plan-for-review artifact - no apply has happened
# under this declaration yet.
#
# R3.2 Step C: adopting the existing, live Foundry resource (rg-RSwan-1970)
# rather than provisioning a duplicate - see the R3.2 plan's Foundry adoption
# Explore section for the exact live values these blocks are modeled from.
# Imported progressively, one resource at a time, not applied as a bulk create.

resource "azurerm_cognitive_account" "foundry" {
  name                          = "rswan-1970-resource"
  resource_group_name           = "rg-RSwan-1970"
  location                      = "eastus2"
  kind                          = "AIServices"
  sku_name                      = "S0"
  custom_subdomain_name         = "rswan-1970-resource"
  public_network_access_enabled = true
  local_auth_enabled            = true
  project_management_enabled    = true

  identity {
    type = "SystemAssigned"
  }

  network_acls {
    default_action = "Allow"
  }
}

resource "azurerm_cognitive_account_project" "reference" {
  cognitive_account_id = azurerm_cognitive_account.foundry.id
  name                 = "rswan-1970"
  location             = "eastus2"

  identity {
    type = "SystemAssigned"
  }
}

resource "azurerm_cognitive_deployment" "gpt5" {
  cognitive_account_id   = azurerm_cognitive_account.foundry.id
  name                   = "gpt-5"
  rai_policy_name        = "Microsoft.DefaultV2"
  version_upgrade_option = "OnceNewDefaultVersionAvailable"

  model {
    format  = "OpenAI"
    name    = "gpt-5"
    version = "2025-08-07"
  }

  sku {
    name     = "GlobalStandard"
    capacity = 50
  }
}

resource "azurerm_cognitive_deployment" "embedding" {
  cognitive_account_id   = azurerm_cognitive_account.foundry.id
  name                   = "text-embedding-3-small"
  rai_policy_name        = "Microsoft.DefaultV2"
  version_upgrade_option = "OnceNewDefaultVersionAvailable"

  model {
    format  = "OpenAI"
    name    = "text-embedding-3-small"
    version = "1"
  }

  sku {
    name     = "Standard"
    capacity = 120
  }
}

resource "azurerm_resource_group" "platform_foundation" {
  name     = "rg-aiml-platform-foundation-dev"
  location = var.location

  tags = {
    product     = "aiml-platform-foundation"
    environment = "dev"
    managed_by  = "r3.2-platform-foundation-terraform"
  }
}

# Premium is required now, not deferred, because Unity Catalog (R3.4) needs it
# and a later tier upgrade would be disruptive - see the R3.2 plan's Databricks
# target Explore section. Unity Catalog itself (metastore assignment, via the
# separate account-level `databricks` provider) is explicitly not part of R3.2.
resource "azurerm_databricks_workspace" "platform_foundation" {
  name                        = "dbw-aiml-platform-foundation-dev"
  resource_group_name         = azurerm_resource_group.platform_foundation.name
  location                    = azurerm_resource_group.platform_foundation.location
  sku                         = "premium"
  managed_resource_group_name = "rg-aiml-platform-foundation-dev-databricks-managed"

  # Explicit, not left to the provider default: matches this repo's established
  # Dev-only network posture (docs/template/security.md - "R1 live acceptance is
  # Dev-only... Development exceptions are explicit"). Private networking for
  # this root is an R3.3+/prod-readiness decision, not silently deferred here.
  public_network_access_enabled = true

  tags = {
    product     = "aiml-platform-foundation"
    environment = "dev"
    managed_by  = "r3.2-platform-foundation-terraform"
  }
}

# R3.2 Step D: platform-administration grants (create/manage) for the apply
# identity, distinct from the runtime/consumer grant below. RBAC declared here
# is not evidence either identity can actually use it - see R3.3.
locals {
  contributor_role_id                    = "/subscriptions/${var.subscription_id}/providers/Microsoft.Authorization/roleDefinitions/b24988ac-6180-42a0-ab88-20f7382dd24c"
  cognitive_services_contributor_role_id = "/subscriptions/${var.subscription_id}/providers/Microsoft.Authorization/roleDefinitions/25fbc0a9-bd7c-42a3-aa1a-3b75d497ee68"
  cognitive_services_openai_user_role_id = "/subscriptions/${var.subscription_id}/providers/Microsoft.Authorization/roleDefinitions/5e0bd9bd-7b93-4f28-af87-19fc36ad61bd"
}

resource "azurerm_role_assignment" "apply_databricks_rg_contributor" {
  name                             = uuidv5("url", "${azurerm_resource_group.platform_foundation.id}|${var.apply_principal_object_id}|${local.contributor_role_id}")
  scope                            = azurerm_resource_group.platform_foundation.id
  role_definition_id               = local.contributor_role_id
  principal_id                     = var.apply_principal_object_id
  principal_type                   = "ServicePrincipal"
  skip_service_principal_aad_check = true
}

resource "azurerm_role_assignment" "apply_foundry_contributor" {
  name                             = uuidv5("url", "${azurerm_cognitive_account.foundry.id}|${var.apply_principal_object_id}|${local.cognitive_services_contributor_role_id}")
  scope                            = azurerm_cognitive_account.foundry.id
  role_definition_id               = local.cognitive_services_contributor_role_id
  principal_id                     = var.apply_principal_object_id
  principal_type                   = "ServicePrincipal"
  skip_service_principal_aad_check = true
}

# Runtime/consumer grant (use, not manage) for the churn reference workload's
# existing compute identity. Databricks-side runtime grant is scoped at R3.3,
# not declared blind here - only the Foundry data-plane grant is known yet.
resource "azurerm_role_assignment" "runtime_foundry_openai_user" {
  name                             = uuidv5("url", "${azurerm_cognitive_account.foundry.id}|${var.compute_principal_object_id}|${local.cognitive_services_openai_user_role_id}")
  scope                            = azurerm_cognitive_account.foundry.id
  role_definition_id               = local.cognitive_services_openai_user_role_id
  principal_id                     = var.compute_principal_object_id
  principal_type                   = "ServicePrincipal"
  skip_service_principal_aad_check = true
}
