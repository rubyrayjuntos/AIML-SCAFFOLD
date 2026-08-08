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

VS Code server definitions are stored in `.vscode/mcp.json`. This file contains commands and endpoints only; it contains no tokens or secrets. Serena is intentionally not configured until its installed command and version are confirmed on the host.

## Codex handoff rule

If an expected MCP server is unavailable in the current client, state that limitation and use the nearest safe CLI or local inspection path. Do not claim that an MCP-backed operation was performed when it was performed through a CLI fallback.

## Documentation changelog

| Version | Created | Modified | Who | Notes |
|---|---|---|---|---|
| 0.1.0 | 2026-08-07 | 2026-08-07 | Ray Swan / Codex | Initial MCP and project-context tooling guidance. |
