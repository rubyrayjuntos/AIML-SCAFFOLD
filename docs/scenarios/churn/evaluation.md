# Churn evaluation

## Corpus-level evaluation

Every training run reports:

- AUC;
- F1;
- accuracy;
- class balance;
- train/test counts;
- missingness and validation results;
- feature schema and dataset lineage.

The promotion policy uses AUC with a minimum improvement threshold of `0.02`, subject to data-quality and lineage gates.

## Account-level evaluation

The drill-down exposes the authoritative served score, feature drivers, previous/current snapshot delta, supporting evidence, and recommended action. The browser never submits its own score or drivers.

## Documentation changelog

| Version | Created | Modified | Who | Notes |
|---|---|---|---|---|
| 0.1.0 | 2026-08-07 | 2026-08-07 | Ray Swan / Codex | Initial churn evaluation definition. |
