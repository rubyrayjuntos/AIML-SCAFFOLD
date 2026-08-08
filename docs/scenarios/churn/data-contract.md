# Churn data contract

## Source

The scenario uses the canonical Telco Customer Churn dataset with exactly 7,043 distinct customers. The ingestion workflow fails closed if the expected source, row count, identifiers, or label domain do not match.

## Layer contract

- Bronze preserves source columns and ingestion metadata.
- Silver normalizes identifiers, numeric fields, and binary churn labels.
- Gold exposes model features, labels, customer context, and governed playbooks.
- ML/ops records feature contracts, evaluation artifacts, lineage, and validation results.

## Prohibited data

Synthetic demo customers, mixed corpora, hardcoded sample accounts, and unlabeled rows cannot enter the training workflow.

## Documentation changelog

| Version | Created | Modified | Who | Notes |
|---|---|---|---|---|
| 0.1.0 | 2026-08-07 | 2026-08-07 | Ray Swan / Codex | Initial churn data contract. |
