from __future__ import annotations

from platform_core.contracts.product_manifest import ProductManifest
from platform_core.contracts.resolver import resolve_project_plan


def test_resolved_plan_explains_ownership_cost_and_defaults(manifest_payload: dict) -> None:
    plan = resolve_project_plan(
        ProductManifest.model_validate(manifest_payload),
        "dev",
        allow_experimental=True,
    )
    assert plan.providers["infrastructure"] == "terraform"
    assert plan.applied_defaults["terraform_state_key"] == "example-risk-dev.tfstate"
    assert plan.environment_topology["dev"]["azure_ml_workspace"] == "mlw-example-risk-dev"
    assert plan.approval_policy == "dev_manual"
    assert plan.azure_context.expected_tenant_id == (
        "00000000-0000-0000-0000-000000000001"
    )
    assert plan.azure_context.deployment_subscription_id == (
        "00000000-0000-0000-0000-000000000000"
    )
    assert plan.azure_context.backend_subscription_id == (
        "00000000-0000-0000-0000-000000000000"
    )
    assert plan.azure_context.cross_subscription_backend is False
    assert plan.azure_context.cross_subscription_backend_allowed is False
    assert plan.azure_context.deployment_identity_client_id_environment_variable == (
        "AZURE_CLIENT_ID"
    )
    assert plan.applied_defaults["data_classification"] == "internal"
    assert plan.provider_extensions == {
        "azure_ml": {
            "location": "eastus",
        }
    }
    assert plan.providers["development"] == "local"
    assert plan.providers["training"] == "local"
    assert plan.providers["serving"] == "local_scoring"
    assert plan.applied_defaults["training_cluster_enabled"] is False
    assert plan.applied_defaults["batch_cluster_enabled"] is False
    assert plan.applied_defaults["compute_identity_required"] is False
    assert plan.maturity_report == {
        "release_status": "preview",
        "manifest_policy": "allow_preview",
        "cli_override_supplied": True,
        "authorization_result": "allowed",
        "remaining_evidence_boundary": "dev_live_pending",
    }
    assert {resource.cost_class.value for resource in plan.resources} == {
        "always_on",
        "job_scoped",
    }
    assert plan.approval_required is True
    assert all(resource.owner != "bicep" for resource in plan.resources)


def test_cloud_training_and_batch_are_independent(manifest_payload: dict) -> None:
    manifest_payload["execution"]["training"]["cloud_fallback"] = {
        "enabled": True,
        "mode": "azure_ml_serverless",
        "instance_type": "Standard_D4s_v7",
        "max_instances": 1,
    }
    plan = resolve_project_plan(
        ProductManifest.model_validate(manifest_payload),
        "dev",
        allow_experimental=True,
    )
    assert plan.applied_defaults["training_serverless_enabled"] is True
    assert plan.applied_defaults["training_cluster_enabled"] is False
    assert plan.applied_defaults["batch_cluster_enabled"] is False
    assert plan.providers["training_cloud"] == "azure_ml_serverless"
    assert "serving_cloud" not in plan.providers


def test_resolved_plan_reports_allowed_cross_subscription_backend(
    manifest_payload: dict,
) -> None:
    manifest_payload["shared_resources"]["azure_context"]["subscription_id"] = (
        "00000000-0000-0000-0000-000000000002"
    )
    manifest_payload["policy"]["allow_cross_subscription_backend"] = True
    plan = resolve_project_plan(
        ProductManifest.model_validate(manifest_payload),
        "dev",
        allow_experimental=True,
    )
    assert plan.azure_context.cross_subscription_backend is True
    assert plan.azure_context.cross_subscription_backend_allowed is True


def test_undeclared_environment_is_rejected(manifest_payload: dict) -> None:
    manifest = ProductManifest.model_validate(manifest_payload)
    try:
        resolve_project_plan(manifest, "prod", allow_experimental=True)
    except ValueError as exc:
        assert "not declared" in str(exc)
    else:
        raise AssertionError("undeclared environment was accepted")
