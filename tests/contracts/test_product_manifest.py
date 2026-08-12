from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from platform_core.contracts.product_manifest import ProductManifest
from platform_core.policy.evaluator import evaluate_policy


def test_ml_only_manifest_does_not_require_foundry(manifest_payload: dict) -> None:
    manifest = ProductManifest.model_validate(manifest_payload)
    assert manifest.capabilities.ml is not None
    assert manifest.agent is None
    assert manifest.tools is None
    descriptors = evaluate_policy(manifest, allow_experimental=True)
    assert {descriptor.capability for descriptor in descriptors} == {
        "infrastructure",
        "ml",
        "registry",
        "serving",
        "evidence",
    }


def test_manifest_loads_from_yaml(tmp_path: Path, manifest_payload: dict) -> None:
    path = tmp_path / "manifest.yaml"
    path.write_text(yaml.safe_dump(manifest_payload), encoding="utf-8")
    assert ProductManifest.load(path).product.name == "example-risk"


@pytest.mark.parametrize("field", ["manifest_schema_version", "platform_version"])
def test_unsupported_versions_fail(field: str, manifest_payload: dict) -> None:
    manifest_payload[field] = "999"
    with pytest.raises(ValidationError, match=field):
        ProductManifest.model_validate(manifest_payload)


def test_invalid_backend_reference_fails(manifest_payload: dict) -> None:
    manifest_payload["shared_resources"]["terraform_backend"]["storage_account_id"] = "name"
    with pytest.raises(ValidationError, match="storage account ARM ID"):
        ProductManifest.model_validate(manifest_payload)


@pytest.mark.parametrize("field", ["tenant_id", "subscription_id"])
def test_invalid_azure_context_uuid_fails(field: str, manifest_payload: dict) -> None:
    manifest_payload["shared_resources"]["azure_context"][field] = "not-a-uuid"
    with pytest.raises(ValidationError, match=field):
        ProductManifest.model_validate(manifest_payload)


def test_backend_subscription_must_be_a_uuid(manifest_payload: dict) -> None:
    backend = manifest_payload["shared_resources"]["terraform_backend"]
    backend["resource_group_id"] = "/subscriptions/not-a-uuid/resourceGroups/state"
    backend["storage_account_id"] = (
        "/subscriptions/not-a-uuid/resourceGroups/state/providers/"
        "Microsoft.Storage/storageAccounts/state"
    )
    with pytest.raises(ValidationError, match="UUID subscription IDs"):
        ProductManifest.model_validate(manifest_payload)


def test_cross_subscription_backend_requires_explicit_policy(
    manifest_payload: dict,
) -> None:
    manifest_payload["shared_resources"]["azure_context"]["subscription_id"] = (
        "00000000-0000-0000-0000-000000000002"
    )
    with pytest.raises(ValidationError, match="allow_cross_subscription_backend"):
        ProductManifest.model_validate(manifest_payload)


def test_cross_subscription_backend_can_be_explicitly_allowed(
    manifest_payload: dict,
) -> None:
    manifest_payload["shared_resources"]["azure_context"]["subscription_id"] = (
        "00000000-0000-0000-0000-000000000002"
    )
    manifest_payload["policy"]["allow_cross_subscription_backend"] = True
    manifest = ProductManifest.model_validate(manifest_payload)
    assert manifest.policy.allow_cross_subscription_backend is True


def test_backend_resource_ids_must_share_subscription(manifest_payload: dict) -> None:
    manifest_payload["shared_resources"]["terraform_backend"]["resource_group_id"] = (
        "/subscriptions/00000000-0000-0000-0000-000000000002/"
        "resourceGroups/rg-platform-state"
    )
    manifest_payload["policy"]["allow_cross_subscription_backend"] = True
    with pytest.raises(ValidationError, match="resource IDs must use the same subscription"):
        ProductManifest.model_validate(manifest_payload)


def test_missing_ml_provider_fails(manifest_payload: dict) -> None:
    manifest_payload["capabilities"]["ml"].pop("provider")
    with pytest.raises(ValidationError, match="provider"):
        ProductManifest.model_validate(manifest_payload)


def test_agent_without_runtime_definition_fails(manifest_payload: dict) -> None:
    manifest_payload["capabilities"]["agent"] = {
        "provider": "foundry",
        "features": ["prompt_agent"],
    }
    with pytest.raises(ValidationError, match="agent definition"):
        ProductManifest.model_validate(manifest_payload)


def test_retrieval_without_provider_fails(manifest_payload: dict) -> None:
    manifest_payload["capabilities"]["retrieval"] = {"features": ["vector_index"]}
    with pytest.raises(ValidationError, match="provider"):
        ProductManifest.model_validate(manifest_payload)


def test_retraining_without_dataset_resolution_is_rejected(manifest_payload: dict) -> None:
    manifest_payload["capabilities"]["ml"]["features"].append("retraining")
    manifest = ProductManifest.model_validate(manifest_payload)
    with pytest.raises(ValueError, match="unsupported R1 ML feature 'retraining'"):
        evaluate_policy(manifest, allow_experimental=True)


@pytest.mark.parametrize("retention", [0, 3651])
def test_invalid_evidence_retention_fails(retention: int, manifest_payload: dict) -> None:
    manifest_payload["policy"]["evidence_retention_days"] = retention
    with pytest.raises(ValidationError, match="evidence_retention_days"):
        ProductManifest.model_validate(manifest_payload)


def test_invalid_region_fails_during_resolution(manifest_payload: dict) -> None:
    manifest_payload["provider_extensions"]["azure_ml"]["location"] = "westus"
    manifest = ProductManifest.model_validate(manifest_payload)
    from platform_core.contracts.resolver import resolve_project_plan

    with pytest.raises(ValueError, match="not allowed"):
        resolve_project_plan(manifest, "dev", allow_experimental=True)


@pytest.mark.parametrize("value", [0, 2, True, "four"])
def test_dev_cloud_compute_is_limited_to_one_node(
    value: object, manifest_payload: dict
) -> None:
    manifest_payload["execution"]["batch"]["cloud_fallback"].update(
        {
            "enabled": True,
            "mode": "azure_ml_cluster",
            "instance_type": "Standard_D4s_v7",
            "max_instances": value,
        }
    )
    with pytest.raises(ValidationError, match="max_instances"):
        ProductManifest.model_validate(manifest_payload)


def test_unknown_azure_ml_extension_key_fails(manifest_payload: dict) -> None:
    manifest_payload["provider_extensions"]["azure_ml"]["compute_sze"] = "typo"
    with pytest.raises(ValidationError, match="compute_sze"):
        ProductManifest.model_validate(manifest_payload)


def test_azure_ml_extensions_are_normalized(manifest_payload: dict) -> None:
    manifest_payload["provider_extensions"]["azure_ml"]["location"] = " EASTUS "
    manifest_payload["execution"]["training"]["cloud_fallback"] = {
        "enabled": True,
        "mode": "azure_ml_serverless",
        "instance_type": " Standard_D4s_v7 ",
    }
    manifest = ProductManifest.model_validate(manifest_payload)
    assert manifest.provider_extensions.azure_ml.location == "eastus"
    assert (
        manifest.execution.training.cloud_fallback.instance_type
        == "Standard_D4s_v7"
    )


def test_local_first_execution_is_the_default(manifest_payload: dict) -> None:
    manifest_payload.pop("execution")
    manifest_payload.pop("cost_policy")
    manifest = ProductManifest.model_validate(manifest_payload)
    assert manifest.execution.development.provider == "local"
    assert manifest.execution.training.cloud_fallback.enabled is False
    assert manifest.execution.batch.cloud_fallback.enabled is False
    assert manifest.cost_policy.cloud_execution_requires_approval is True
    assert manifest.cost_policy.default_max_nodes == 1


@pytest.mark.parametrize("target", ["training", "batch"])
def test_enabled_cloud_compute_requires_explicit_instance_type(
    target: str, manifest_payload: dict
) -> None:
    manifest_payload["execution"][target]["cloud_fallback"] = {
        "enabled": True,
        "mode": "azure_ml_serverless" if target == "training" else "azure_ml_cluster",
    }
    with pytest.raises(ValidationError, match="explicit mode and instance_type"):
        ProductManifest.model_validate(manifest_payload)


def test_disabled_cloud_compute_rejects_latent_sku(manifest_payload: dict) -> None:
    manifest_payload["execution"]["training"]["cloud_fallback"]["instance_type"] = (
        "Standard_D4s_v7"
    )
    with pytest.raises(ValidationError, match="enabled=true"):
        ProductManifest.model_validate(manifest_payload)


def test_old_implicit_compute_extension_is_rejected(manifest_payload: dict) -> None:
    manifest_payload["provider_extensions"]["azure_ml"]["compute_size"] = (
        "Standard_D4s_v5"
    )
    with pytest.raises(ValidationError, match="compute_size"):
        ProductManifest.model_validate(manifest_payload)


def test_stable_only_rejects_preview_provider(manifest_payload: dict) -> None:
    manifest_payload["policy"]["capability_maturity"] = "stable_only"
    manifest = ProductManifest.model_validate(manifest_payload)
    with pytest.raises(ValueError, match="exceeds policy"):
        evaluate_policy(manifest, allow_experimental=True)


def test_preview_requires_explicit_cli_opt_in(manifest_payload: dict) -> None:
    manifest = ProductManifest.model_validate(manifest_payload)
    with pytest.raises(ValueError, match="--allow-experimental"):
        evaluate_policy(manifest)


def test_planned_agent_provider_is_unavailable(manifest_payload: dict) -> None:
    manifest_payload["capabilities"]["agent"] = {
        "provider": "foundry",
        "features": ["prompt_agent"],
    }
    manifest_payload["agent"] = {
        "name": "helper",
        "description": "A helper",
        "tools": ["lookup"],
        "output_schema": "schema.json",
        "guardrails": {"require_citations": True},
    }
    manifest = ProductManifest.model_validate(manifest_payload)
    with pytest.raises(ValueError, match="planned and unavailable"):
        evaluate_policy(manifest, allow_experimental=True)


def test_retrieval_without_scenario_fails(manifest_payload: dict) -> None:
    manifest_payload["capabilities"]["retrieval"] = {
        "provider": "azure_ai_search",
        "features": ["vector_index"],
    }
    with pytest.raises(ValidationError, match="scenario retrieval"):
        ProductManifest.model_validate(manifest_payload)


def test_bicep_is_not_an_r1_provider(manifest_payload: dict) -> None:
    manifest_payload["infrastructure"]["azure"]["provider"] = "bicep"
    manifest = ProductManifest.model_validate(manifest_payload)
    with pytest.raises(ValueError, match="Terraform is the only"):
        evaluate_policy(manifest, allow_experimental=True)


def test_duplicate_features_fail(manifest_payload: dict) -> None:
    manifest_payload["capabilities"]["ml"]["features"].append("training")
    with pytest.raises(ValidationError, match="unique"):
        ProductManifest.model_validate(manifest_payload)


def test_platform_core_contains_no_reference_scenario_names() -> None:
    root = Path("src/platform_core")
    forbidden = ("churn", "taxi", "telco")
    for path in root.rglob("*.py"):
        source = path.read_text(encoding="utf-8").lower()
        for token in forbidden:
            assert token not in source, f"{token!r} leaked into {path}"
