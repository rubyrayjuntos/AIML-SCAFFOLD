from __future__ import annotations

from platform_core.contracts.product_manifest import ProductManifest
from platform_core.contracts.project_plan import (
    PlannedResource,
    ResolvedAzureContext,
    ResolvedProjectPlan,
    ResourceCostClass,
)
from platform_core.policy.evaluator import evaluate_policy


def resolve_project_plan(
    manifest: ProductManifest,
    environment: str,
    *,
    allow_experimental: bool = False,
) -> ResolvedProjectPlan:
    if environment not in manifest.environments:
        raise ValueError(
            f"environment {environment!r} is not declared; expected one of {manifest.environments}"
        )
    descriptors = evaluate_policy(manifest, allow_experimental=allow_experimental)
    extension = manifest.provider_extensions.azure_ml
    location = extension.location or manifest.policy.allowed_regions[0]
    if location not in manifest.policy.allowed_regions:
        raise ValueError(
            f"Azure ML location {location!r} is not allowed by policy "
            f"{manifest.policy.allowed_regions}"
        )
    training_cloud = manifest.execution.training.cloud_fallback
    batch_cloud = manifest.execution.batch.cloud_fallback
    training_cluster_enabled = (
        training_cloud.enabled and training_cloud.mode == "azure_ml_cluster"
    )
    training_serverless_enabled = (
        training_cloud.enabled and training_cloud.mode == "azure_ml_serverless"
    )
    batch_cluster_enabled = batch_cloud.enabled
    monitoring_enabled = manifest.execution.monitoring.enabled
    azure_context = manifest.shared_resources.azure_context
    backend_subscription = manifest.shared_resources.terraform_backend.subscription_id
    deployment_subscription = str(azure_context.subscription_id).lower()

    resources = [
        PlannedResource(
            kind="azure_ml_workspace",
            owner="terraform",
            cost_class=ResourceCostClass.ALWAYS_ON,
            notes="Project and environment isolated.",
        ),
        PlannedResource(
            kind="storage_account",
            owner="terraform",
            cost_class=ResourceCostClass.ALWAYS_ON,
            notes="Contains Azure ML assets and the private platform-evidence container.",
        ),
        PlannedResource(
            kind="key_vault",
            owner="terraform",
            cost_class=ResourceCostClass.ALWAYS_ON,
        ),
        PlannedResource(
            kind="log_analytics_and_application_insights",
            owner="terraform",
            cost_class=ResourceCostClass.ALWAYS_ON,
        ),
        PlannedResource(
            kind="local_ml_lifecycle",
            owner="generated_project",
            cost_class=ResourceCostClass.JOB_SCOPED,
            notes="Default Dev prepare, train, evaluate, package, score, and evidence path.",
        ),
    ]
    if training_serverless_enabled:
        resources.append(
            PlannedResource(
                kind="azure_ml_serverless_training_jobs",
                owner="azure_ml",
                cost_class=ResourceCostClass.JOB_SCOPED,
                notes="Charged only when explicitly authorized and submitted.",
            )
        )
    if training_cluster_enabled:
        resources.append(
            PlannedResource(
                kind="azure_ml_training_compute",
                owner="terraform",
                cost_class=ResourceCostClass.SCALE_TO_ZERO,
                notes="Explicit SKU; zero minimum and one-node Dev maximum.",
            )
        )
    if batch_cluster_enabled:
        resources.append(
            PlannedResource(
                kind="azure_ml_batch_compute",
                owner="terraform",
                cost_class=ResourceCostClass.SCALE_TO_ZERO,
                notes="Explicit SKU; zero minimum and one-node Dev maximum.",
            )
        )
    if monitoring_enabled:
        resources.append(
            PlannedResource(
                kind="monitoring_storage_container",
                owner="terraform",
                cost_class=ResourceCostClass.ALWAYS_ON,
                notes="Baseline snapshot and inference-log evidence for drift detection.",
            )
        )
    providers = {
        "infrastructure": "terraform",
        "development": "local",
        "training": "local",
        "registry": "azure_ml",
        "serving": "local_scoring",
        "evidence": "azure_blob",
    }
    if training_cloud.enabled:
        providers["training_cloud"] = str(training_cloud.mode)
    if batch_cloud.enabled:
        providers["serving_cloud"] = "azure_ml_batch"
    return ResolvedProjectPlan(
        manifest_schema_version=manifest.manifest_schema_version,
        platform_version=manifest.platform_version,
        project=manifest.product.name,
        environment=environment,
        azure_context=ResolvedAzureContext(
            expected_tenant_id=str(azure_context.tenant_id).lower(),
            deployment_subscription_id=deployment_subscription,
            backend_subscription_id=backend_subscription,
            cross_subscription_backend=backend_subscription != deployment_subscription,
            cross_subscription_backend_allowed=(
                manifest.policy.allow_cross_subscription_backend
            ),
            deployment_identity_client_id_environment_variable=(
                azure_context.deployment_identity.client_id_environment_variable
            ),
            deployment_identity_object_id_environment_variable=(
                azure_context.deployment_identity.object_id_environment_variable
            ),
            oidc_issuer=azure_context.deployment_identity.federated_credential.issuer,
            oidc_subject=azure_context.deployment_identity.federated_credential.subject,
            oidc_audience=azure_context.deployment_identity.federated_credential.audience,
        ),
        environment_topology={
            name: {
                "resource_group": f"rg-{manifest.product.name}-{name}",
                "terraform_state_key": f"{manifest.product.name}-{name}.tfstate",
                "azure_ml_workspace": f"mlw-{manifest.product.name}-{name}",
                "evidence_container": "platform-evidence",
            }
            for name in manifest.environments
        },
        providers=providers,
        capabilities=descriptors,
        applied_defaults={
            "location": location,
            "execution": manifest.execution.model_dump(mode="json"),
            "cost_policy": manifest.cost_policy.model_dump(mode="json"),
            "training_cluster_enabled": training_cluster_enabled,
            "training_serverless_enabled": training_serverless_enabled,
            "batch_cluster_enabled": batch_cluster_enabled,
            "monitoring_enabled": monitoring_enabled,
            "compute_identity_required": (
                training_cluster_enabled or batch_cluster_enabled
            ),
            "evidence_retention_days": manifest.policy.evidence_retention_days,
            "terraform_state_key": f"{manifest.product.name}-{environment}.tfstate",
            "capability_maturity_policy": manifest.policy.capability_maturity.value,
            "data_classification": manifest.policy.data_classification,
            "allowed_regions": manifest.policy.allowed_regions,
        },
        shared_resources=manifest.shared_resources.model_dump(mode="json"),
        provider_extensions=manifest.provider_extensions.model_dump(
            mode="json", exclude_none=True
        ),
        generated_components=[
            "terraform",
            "local_ml_lifecycle",
            "local_scoring",
            "azure_ml_registry",
            "azure_blob_evidence",
            "github_actions",
        ]
        + (["azure_ml_training"] if training_cloud.enabled else [])
        + (["azure_ml_batch"] if batch_cloud.enabled else [])
        + (["azure_ml_monitoring"] if monitoring_enabled else []),
        resources=resources,
        preconditions=[
            "Environment resource group exists.",
            "Terraform backend exists and is reachable.",
            "GitHub OIDC deployment identity has scoped environment permissions.",
            "Exact regional SKU availability and quota are verified when cloud compute is enabled.",
            "Each charged cloud compute workflow receives deliberate authorization.",
        ],
        warnings=[
            "R1 providers remain preview until the Dev clean-room proof succeeds.",
            "Local lifecycle evidence does not prove Azure ML execution, identity, "
            "lineage, registration, or batch serving.",
            "Bicep, online serving, automated retraining, Foundry, Search, and "
            "Databricks are excluded."
            + (
                " Manually-triggered batch input-drift detection is included when "
                "monitoring is enabled; it never triggers retraining automatically."
                if monitoring_enabled
                else " Input-drift detection is excluded unless monitoring is enabled."
            ),
        ],
        approval_required=True,
        approval_policy=manifest.policy.deployment_approval,
        maturity_report={
            "release_status": "preview",
            "manifest_policy": manifest.policy.capability_maturity.value,
            "cli_override_supplied": allow_experimental,
            "authorization_result": "allowed",
            "remaining_evidence_boundary": "dev_live_pending",
        },
    )
