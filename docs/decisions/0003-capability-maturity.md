# ADR 0003: Capability maturity is explicit and enforced

## Decision

Every provider capability is classified as `stable`, `preview`, `experimental`, or `planned`.

- `stable`: clean-room live path has passed its acceptance suite.
- `preview`: implemented with partial live evidence.
- `experimental`: implemented contract or provider prototype without sufficient live evidence.
- `planned`: schema-reserved and unavailable.

The default manifest policy is `stable_only`. Preview or experimental capabilities require an explicit policy and the CLI `--allow-experimental` switch. Planned capabilities are always rejected.

R1 registers Terraform infrastructure, Azure ML training/evaluation/registry/batch serving, Azure Blob evidence, and shared policy evaluation. Their release status remains preview until the R1 clean-room Dev proof promotes them to stable.

## Documentation changelog

| Version | Created | Modified | Who | Notes |
|---|---|---|---|---|
| 0.1.0 | 2026-08-11 | 2026-08-11 | Ray Swan / Codex | Established the provider capability maturity model and generation gates. |
