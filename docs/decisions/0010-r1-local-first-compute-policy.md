# ADR 0010: R1 local-first compute policy

## Decision

R1 Dev execution defaults to local, container-capable execution. The generated local runner invokes the same prepare, train, evaluate, promotion, packaging, and scoring implementation used by the Azure ML adapter and emits the same normalized evidence shape to a local sink.

Azure training and Azure batch compute are independent manifest choices:

- training can enable Azure ML serverless or a project-owned scale-to-zero cluster;
- batch can enable a project-owned scale-to-zero cluster;
- an enabled cloud path requires an explicit instance type;
- the factory never infers or substitutes a VM SKU;
- every Dev cluster has zero minimum nodes and exactly one maximum node;
- cloud workflows are generated only for enabled paths and require a cost-aware authorization phrase before submission.

The default local-first Terraform graph still creates the Azure ML workspace, storage/evidence boundary, Key Vault, observability, workspace-storage role, and workflow-storage role. It does not create a compute cluster, compute identity, or compute-storage role. Those resources are conditional on cluster compute.

Azure ML remains the R1 cloud provider and registry authority. Local validation does not establish Azure ML job submission, managed identity access, lineage, registration, endpoint deployment, or batch invocation evidence.

## Rationale

The rejected candidate exposed that mandatory clusters and an implicit `Standard_D4s_v5` default coupled development correctness to subscription-specific capacity. Local routine validation needs no Azure compute. Cloud execution is therefore an intentional, cost-governed escalation rather than a factory prerequisite.

Azure ML pipelines cannot use local compute as their pipeline target, so the local path is a separate orchestration adapter over shared lifecycle code rather than a `compute: local` edit to the cloud pipeline. Azure ML serverless pipeline execution uses `azureml:serverless` and an explicit one-node instance request when selected.

## Consequences

- A base infrastructure plan requests no compute-family quota and creates fewer resources than the rejected compute-bound candidate.
- Exact SKU availability and quota are checked only when a cloud fallback is explicitly enabled.
- Changes to execution or cost policy alter the resolved plan, provenance digests, and generation identity.
- A cloud workflow dispatch is still a separate authorization boundary after infrastructure exists.
- Production sizing, shared cluster policy, private networking, and broader workload isolation remain outside R1.

## Documentation changelog

| Version | Created | Modified | Who | Notes |
|---|---|---|---|---|
| 1.0.0 | 2026-08-12 | 2026-08-12 | Ray Swan / Codex | Established local-first Dev execution, independent explicit Azure compute fallbacks, one-node ceiling, conditional Terraform ownership, and cost-aware workflow authorization. |
