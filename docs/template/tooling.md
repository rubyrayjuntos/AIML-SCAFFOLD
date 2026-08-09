# Development tooling and context servers

## Recommended server roles

Use the following MCP roles when the client supports them:

- **Azure MCP** — resource groups, Azure resources, RBAC, networking, storage, Key Vault, and deployment context.
- **Foundry MCP** — Foundry projects, model deployments, agents, tools, evaluations, and grounding configuration.
- **Azure DevOps MCP** — Azure DevOps work items, repositories, pipelines, tests, and project artifacts when Azure DevOps is part of the delivery environment.
- **Serena or an equivalent semantic context server** — project-aware symbol search, dependency navigation, and scoped repository context.

## Fallbacks

Local `az`, `databricks`, `terraform`, `git`, `rg`, and repository tests remain valid fallbacks. Authentication must use the active Entra/CLI session or CI OIDC; credentials must not be placed in repository configuration.

## Client configuration

VS Code server definitions are stored in `.vscode/mcp.json`. This file contains commands and endpoints only; it contains no tokens or secrets. Serena is configured in `.serena/project.yml` with Python, Terraform, Markdown, and Bash language support. YAML editing remains covered by the recommended VS Code YAML extension and repository validation commands. The VS Code MCP definition starts Serena with `--project-from-cwd`, so the repository-local project configuration is selected automatically. Serena's cache remains untracked through `.serena/.gitignore`.

## Codex handoff rule

If an expected MCP server is unavailable in the current client, state that limitation and use the nearest safe CLI or local inspection path. Do not claim that an MCP-backed operation was performed when it was performed through a CLI fallback.

## Documentation changelog

| Version | Created | Modified | Who | Notes |
|---|---|---|---|---|
| 0.2.0 | 2026-08-07 | 2026-08-07 | Ray Swan / Codex | Added repository-scoped Serena configuration and automatic current-workspace project binding. |
| 0.1.0 | 2026-08-07 | 2026-08-07 | Ray Swan / Codex | Initial MCP and project-context tooling guidance. |
