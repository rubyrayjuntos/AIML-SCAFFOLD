# Extension guide: adding a new scenario

## Goal

Add a new ML scenario without modifying `platform_core` or copying the churn implementation.

## Required steps

1. Create `src/scenarios/<name>/scenario.yaml`.
2. Define source datasets and the data-quality contract.
3. Implement the scenario feature builder and register a feature version/contract.
4. Implement the task adapter for the supported task type.
5. Define evaluation metrics, gates, and promotion policy.
6. Define serving and Foundry retrieval/tool configuration.
7. Add unit, data-quality, contract, and integration tests.
8. Add a scenario runbook and demo flow.

## Completion criteria

A scenario is complete when it can run the generic workflow from ingestion through serving without changes to reusable contracts, gates, lifecycle logic, or API envelope behavior.

## Example future scenarios

- fraud classification;
- equipment-failure classification;
- demand forecasting;
- recommendation ranking;
- document routing.

## Documentation changelog

| Version | Created | Modified | Who | Notes |
|---|---|---|---|---|
| 0.1.0 | 2026-08-07 | 2026-08-07 | Ray Swan / Codex | Initial scenario extension guide. |
