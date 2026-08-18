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

output "foundry_account_id" {
  description = "Azure resource ID of the adopted Foundry (AIServices) account."
  value       = azurerm_cognitive_account.foundry.id
}

output "foundry_endpoint" {
  description = "Base Cognitive Services endpoint for the Foundry account."
  value       = azurerm_cognitive_account.foundry.endpoint
}

# Stable correlation dimension for later OpenTelemetry work (R5) - the
# account's own system-assigned identity, not a secret. See the R3.2 plan's
# Outputs/contracts non-functional requirement: this root must not foreclose
# later cross-service tracing, without instrumenting anything now.
output "foundry_identity_principal_id" {
  description = "Principal ID of the Foundry account's system-assigned managed identity."
  value       = azurerm_cognitive_account.foundry.identity[0].principal_id
}

output "foundry_deployment_gpt5_id" {
  description = "Azure resource ID of the gpt-5 Foundry deployment."
  value       = azurerm_cognitive_deployment.gpt5.id
}

output "foundry_deployment_gpt5_name" {
  description = "Deployment name for gpt-5 (used as the model identifier in API calls)."
  value       = azurerm_cognitive_deployment.gpt5.name
}

output "foundry_deployment_embedding_id" {
  description = "Azure resource ID of the text-embedding-3-small Foundry deployment."
  value       = azurerm_cognitive_deployment.embedding.id
}

output "foundry_deployment_embedding_name" {
  description = "Deployment name for text-embedding-3-small (used as the model identifier in API calls)."
  value       = azurerm_cognitive_deployment.embedding.name
}
