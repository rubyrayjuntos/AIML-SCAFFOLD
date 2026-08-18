# ADR 0005: R1 project topology and release boundary

## Decision

One generated repository represents one ML product. It can define Dev, Test, and Prod, but each environment uses an independent resource group, Terraform state key, Azure ML workspace, storage account, identity boundary, and evidence container.

R1 live acceptance covers Dev only and ends at infrastructure, training, evaluation, conditional registration, explicit-version batch deployment, batch invocation, and evidence. Online endpoints, monitoring, retraining, Foundry, Search, Databricks, hybrid composition, and portfolio controls are later releases.

GitHub Actions and Azure ML jobs orchestrate R1. AKS is not an R1 dependency.

## Documentation changelog

| Version | Created | Modified | Who | Notes |
|---|---|---|---|---|
| 0.1.0 | 2026-08-11 | 2026-08-11 | Ray Swan / Codex | Fixed repository/environment ownership and the Dev-only batch R1 boundary. |
