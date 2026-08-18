output "environment_resource_group_id" {
  value = azurerm_resource_group.environment.id
}

output "backend_container_resource_id" {
  value = azurerm_storage_container.state.id
}
