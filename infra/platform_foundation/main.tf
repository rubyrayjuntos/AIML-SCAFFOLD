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
