output "application_client_id" {
  value = azuread_application.github.client_id
}

output "application_object_id" {
  value = azuread_application.github.object_id
}

output "application_id" {
  description = "Full Microsoft Graph resource ID (/applications/{object_id}), as required by azuread_application_federated_identity_credential.application_id."
  value       = azuread_application.github.id
}

output "service_principal_object_id" {
  value = azuread_service_principal.github.object_id
}

output "federated_subject" {
  value = azuread_application_federated_identity_credential.github_environment.subject
}
