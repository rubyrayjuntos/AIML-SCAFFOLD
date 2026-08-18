# Unlike modules/github_prerequisites, this module does NOT create/manage the
# repository resource itself - it targets AIML-SCAFFOLD, the factory's own
# source repository, which already exists with real history and content.
# Managing it as a Terraform-owned github_repository resource (with
# archive_on_destroy/prevent_destroy semantics meant for a disposable
# generated-project repo) would be wrong for the repo this code itself lives
# in. Only the environment and its variables are Terraform-owned here.

resource "github_repository_environment" "this" {
  repository  = var.repository_name
  environment = var.environment_name

  deployment_branch_policy {
    protected_branches     = true
    custom_branch_policies = false
  }
}

resource "github_actions_environment_variable" "context" {
  for_each = var.variables

  repository    = var.repository_name
  environment   = github_repository_environment.this.environment
  variable_name = each.key
  value         = each.value
}
