# ADR 0001: Bicep is authoritative; Terraform is portability-only

We use Bicep as the supported Azure deployment path because this repository is Azure-first and must demonstrate native Azure resource modeling and `what-if` validation.

Terraform is maintained as a separately validated portability implementation. It must target a separate resource group/state and must never manage resources also managed by Bicep.

## Documentation changelog

| Version | Created | Modified | Who | Notes |
|---|---|---|---|---|
| 0.1.0 | 2026-08-07 | 2026-08-07 | Ray Swan / Codex | Initial infrastructure-as-code ownership decision. |
