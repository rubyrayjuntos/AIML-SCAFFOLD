# Churn feature catalog

## Feature contract

- Version: `churn.features.v1`
- Contract: `churn_feature_contract_v1`
- Builder: `churn_feature_builder`

## Initial features

| Feature | Type | Meaning | Source layer |
|---|---|---|---|
| `tenure_months` | integer | Customer tenure | silver |
| `MonthlyCharges` | double | Current monthly charge | silver |
| `TotalCharges` | double | Accumulated charge | silver |
| `SeniorCitizen` | integer | Source demographic flag | silver |
| `Contract` | string | Contract type | silver |
| `InternetService` | string | Internet service type | silver |
| `TechSupport` | string | Technical support subscription | silver |

Feature changes require a new feature version, updated training lineage, and evaluation comparison.

## Documentation changelog

| Version | Created | Modified | Who | Notes |
|---|---|---|---|---|
| 0.1.0 | 2026-08-07 | 2026-08-07 | Ray Swan / Codex | Initial churn feature catalog. |
