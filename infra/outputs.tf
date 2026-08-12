output "github_repository" {
  description = "Created GitHub repository name with owner."
  value       = "${var.github_owner}/${module.github_prerequisites.repository_name}"
}

output "github_environment" {
  description = "Protected GitHub deployment environment."
  value       = module.github_prerequisites.environment_name
}

output "azure_client_id" {
  description = "Application/client ID for generated GitHub workflows."
  value       = module.entra_identity.application_client_id
}

output "azure_client_object_id" {
  description = "Service-principal/object ID for Azure RBAC and doctor."
  value       = module.entra_identity.service_principal_object_id
}

output "federated_subject" {
  description = "Exact GitHub Actions subject configured in Entra."
  value       = module.entra_identity.federated_subject
}

output "environment_resource_group_id" {
  description = "Administrator-owned R1 Dev environment resource group."
  value       = module.azure_foundation.environment_resource_group_id
}

output "backend_container_resource_id" {
  description = "Dedicated Terraform state container resource ID."
  value       = module.azure_foundation.backend_container_resource_id
}
