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
    compute_size = extension.compute_size or "Standard_D4s_v5"
    batch_max = extension.batch_compute_max_instances or 4
    training_max = extension.training_compute_max_instances or 4
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
            kind="azure_ml_training_compute",
            owner="terraform",
            cost_class=ResourceCostClass.SCALE_TO_ZERO,
        ),
        PlannedResource(
            kind="azure_ml_batch_compute",
            owner="terraform",
            cost_class=ResourceCostClass.SCALE_TO_ZERO,
        ),
        PlannedResource(
            kind="azure_ml_training_and_batch_jobs",
            owner="azure_ml",
            cost_class=ResourceCostClass.JOB_SCOPED,
        ),
    ]
    providers = {
        "infrastructure": "terraform",
        "training": "azure_ml",
        "registry": "azure_ml",
        "serving": "azure_ml_batch",
        "evidence": "azure_blob",
    }
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
            "compute_size": compute_size,
            "batch_compute_max_instances": batch_max,
            "training_compute_max_instances": training_max,
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
            "azure_ml_training",
            "azure_ml_registry",
            "azure_ml_batch",
            "azure_blob_evidence",
            "github_actions",
        ],
        resources=resources,
        preconditions=[
            "Environment resource group exists.",
            "Terraform backend exists and is reachable.",
            "GitHub OIDC deployment identity has scoped environment permissions.",
            "Azure ML and required regional VM quota are available.",
        ],
        warnings=[
            "R1 providers remain preview until the Dev clean-room proof succeeds.",
            "Bicep, online serving, monitoring, retraining, Foundry, Search, and "
            "Databricks are excluded.",
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
