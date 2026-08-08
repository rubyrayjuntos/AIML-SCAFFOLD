# Churn reference scenario

This is the executable reference scenario for the enterprise ML workflow template. It demonstrates customer churn evaluation, corpus-level model metrics, customer-level drill-down, MLflow lifecycle management, Databricks delivery, CI/CD, and Foundry grounded explanation.

## Scenario boundaries

- Source: canonical 7,043-record Telco Customer Churn corpus.
- Task: binary classification.
- Entity: `customer_id`.
- Features: governed and versioned through the feature registry.
- Model: registered in Unity Catalog and served through Databricks Model Serving.
- Explanation: Foundry agent using approved score, diff, evidence, and playbook tools.

## Reference files

- [Scenario manifest](scenario.yaml)
- [Data contract](data-contract.md)
- [Feature catalog](feature-catalog.md)
- [Evaluation](evaluation.md)
- [Demo runbook](demo-runbook.md)

## Non-goals

The scenario does not redefine platform lifecycle, security, deployment, response-envelope, or monitoring contracts.

## Documentation changelog

| Version | Created | Modified | Who | Notes |
|---|---|---|---|---|
| 0.1.0 | 2026-08-07 | 2026-08-07 | Ray Swan / Codex | Initial churn scenario documentation. |
