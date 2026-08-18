# R3.2 Step B (see docs/superpowers/plans/r3.2-platform-foundation.md and
# ADR 0012). This is a saved-plan-for-review artifact - no apply has happened
# under this declaration yet.
#
# Foundry adoption/import (Step C) and RBAC (Step D) remain separate,
# not-yet-authorized cycles - not declared here.

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

  tags = {
    product     = "aiml-platform-foundation"
    environment = "dev"
    managed_by  = "r3.2-platform-foundation-terraform"
  }
}
