# ADR 0001: Bicep is authoritative; Terraform is portability-only

We use Bicep as the supported Azure deployment path because this repository is Azure-first and must demonstrate native Azure resource modeling and `what-if` validation.

Terraform is maintained as a separately validated portability implementation. It must target a separate resource group/state and must never manage resources also managed by Bicep.
