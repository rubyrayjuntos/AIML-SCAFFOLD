resource "azuread_application" "github" {
  display_name     = var.application_display_name
  sign_in_audience = "AzureADMyOrg"
  owners           = [var.application_owner_object_id]
}

resource "azuread_service_principal" "github" {
  client_id                    = azuread_application.github.client_id
  account_enabled              = true
  app_role_assignment_required = false
  owners                       = [var.application_owner_object_id]
}

resource "azuread_application_federated_identity_credential" "github_environment" {
  application_id = azuread_application.github.id
  display_name   = var.federated_credential_name
  description    = "GitHub protected Dev environment for Azure AI ML Ops R1."
  audiences      = ["api://AzureADTokenExchange"]
  issuer         = "https://token.actions.githubusercontent.com"
  subject        = var.federated_subject
}
