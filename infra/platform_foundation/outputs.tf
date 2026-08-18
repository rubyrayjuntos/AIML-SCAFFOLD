# Consumers receive these through their own declared configuration
# (e.g. scenario.yaml), populated at generation/config time - never via
# terraform_remote_state coupling one root to another's state. See the R3.2
# plan's Outputs/contracts section and ADR 0011's no-accidental-inheritance
# invariant.

output "databricks_workspace_id" {
  description = "Azure resource ID of the platform_foundation Databricks workspace."
  value       = azurerm_databricks_workspace.platform_foundation.id
}

output "databricks_workspace_url" {
  description = "Workspace URL for the platform_foundation Databricks workspace."
  value       = azurerm_databricks_workspace.platform_foundation.workspace_url
}
