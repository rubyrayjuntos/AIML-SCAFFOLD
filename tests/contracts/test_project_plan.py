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
            "compute_size": "Standard_D4s_v5",
            "batch_compute_max_instances": 4,
        }
    }
    assert plan.maturity_report == {
        "release_status": "preview",
        "manifest_policy": "allow_preview",
        "cli_override_supplied": True,
        "authorization_result": "allowed",
        "remaining_evidence_boundary": "dev_live_pending",
    }
    assert {resource.cost_class.value for resource in plan.resources} == {
        "always_on",
        "scale_to_zero",
        "job_scoped",
    }
    assert plan.approval_required is True
    assert all(resource.owner != "bicep" for resource in plan.resources)


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
