# Azure ML R1 capability ledger

The ledger separates code presence from live evidence. Extraction does not upgrade maturity; only the clean-room acceptance run can do that.

| Capability | Reference code | Evidence currently available | Extraction source | R1 state |
|---|---|---|---|---|
| Terraform infrastructure | `azure-mlops` `c6cbbfb`; project template `7312ebc` | Dev and Prod reference deployments recorded; no R1 clean-room proof | Compare instance against template and retain verified fixes | Preview candidate |
| Training | `azure-mlops` `c6cbbfb` | Dev and Prod reference runs recorded | Instance pipeline and shared workflow contract | Preview candidate |
| Evaluation | `azure-mlops` `c6cbbfb` | Reference metrics and promotion gate recorded | Instance `evaluate.py`; scenario logic stays outside `platform_core` | Preview candidate |
| Conditional registration | `azure-mlops` `c6cbbfb` | Normal training path exercised | Instance `register.py`; template copy is rejected because it contains `deploy_flag=1` | Preview candidate |
| Batch deployment | `azure-mlops` `c6cbbfb` | Dev and Prod endpoint evidence recorded | Instance batch YAML/scorer plus pinned shared workflows | Preview candidate |
| Project-local evidence | Monitoring container and inference evidence in `azure-mlops` | Dev evidence exists for monitoring artifacts, not the normalized R1 contract | New shared EvidenceEvent contract and Blob sink | Preview |
| Online endpoint | `azure-mlops` | Dev evidence only | Not extracted in R1 | Preview, excluded |
| Healthy monitoring | `azure-mlops` | Dev healthy/no-retrain branch | Not extracted in R1 | Preview, excluded |
| Drift and retraining | `azure-mlops` | Static/local plus incomplete reaction-path evidence | Not extracted in R1 | Experimental, excluded |
| Foundry, Search, Databricks | AIML-SCAFFOLD contracts/prototypes | No R1 provider proof | No R1 provider registration | Planned, excluded |

## Extraction rules

- Scenario-specific taxi code is evidence, not reusable platform code.
- The project instance wins over a stale template only when the ledger names the corrective commit and supporting test/evidence.
- R1 generates repository-local workflows with commit-pinned actions and pinned CLI/SDK versions. Any later shared workflow reference must use an immutable release before GA.
- Maturity becomes `stable` only after a generated Dev project succeeds without source repair.

## Documentation changelog

| Version | Created | Modified | Who | Notes |
|---|---|---|---|---|
| 0.2.0 | 2026-08-11 | 2026-08-11 | Ray Swan / Codex | Clarified the generated local-workflow and immutable dependency boundary. |
| 0.1.0 | 2026-08-11 | 2026-08-11 | Ray Swan / Codex | Classified Azure ML reference capabilities and selected R1 extraction sources. |
