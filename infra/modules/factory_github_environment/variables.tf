variable "repository_name" {
  description = "Name of the existing repository (not managed by this module) to configure an environment on."
  type        = string
}

variable "environment_name" {
  type = string
}

variable "variables" {
  description = "GitHub Actions environment variables to set (identifiers, not secrets - e.g. AZURE_CLIENT_ID, APPLY_AUTHORIZED_ACTORS)."
  type        = map(string)
}
