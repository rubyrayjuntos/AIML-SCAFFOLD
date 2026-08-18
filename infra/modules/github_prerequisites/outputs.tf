output "repository_name" {
  value = github_repository.generated.name
}

output "repository_url" {
  value = github_repository.generated.html_url
}

output "environment_name" {
  value = github_repository_environment.dev.environment
}
