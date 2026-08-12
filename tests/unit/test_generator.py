from __future__ import annotations

import importlib.util
import json
import shutil
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import ModuleType

import pytest
import yaml

from aiml_scaffold.doctor import doctor_project
from aiml_scaffold.generator import (
    generate_project,
    generated_files_digest,
    template_digest,
    verify_generation,
)
from platform_core.contracts.product_manifest import ProductManifest


def _tree(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }


def _load_module(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location("generated_plan_artifact", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_generation_is_byte_stable(tmp_path: Path, manifest_payload: dict) -> None:
    manifest = ProductManifest.model_validate(manifest_payload)
    first = tmp_path / "first"
    second = tmp_path / "second"
    _, first_receipt = generate_project(manifest, first, allow_experimental=True)
    _, second_receipt = generate_project(manifest, second, allow_experimental=True)
    assert _tree(first) == _tree(second)
    assert first_receipt == second_receipt
    assert verify_generation(first)["generation_id"] == first_receipt["generation_id"]
    assert not any("__pycache__" in path.parts for path in first.rglob("*"))


def test_generation_binds_platform_source_and_package(
    tmp_path: Path, manifest_payload: dict
) -> None:
    output = tmp_path / "project"
    _, receipt = generate_project(
        ProductManifest.model_validate(manifest_payload),
        output,
        allow_experimental=True,
        platform_source_commit="a" * 40,
        platform_package_digest="sha256:" + "b" * 64,
    )
    assert receipt["platform_source_commit"] == "a" * 40
    assert receipt["platform_package_digest"] == "sha256:" + "b" * 64
    assert verify_generation(output)["generation_id"] == receipt["generation_id"]
    generated_verifier = _load_module(output / "scripts/verify_generation.py")
    assert generated_verifier.verify(output)["generation_id"] == receipt["generation_id"]


def test_generation_rejects_partial_platform_provenance(
    tmp_path: Path, manifest_payload: dict
) -> None:
    with pytest.raises(ValueError, match="must be supplied together"):
        generate_project(
            ProductManifest.model_validate(manifest_payload),
            tmp_path / "project",
            allow_experimental=True,
            platform_source_commit="a" * 40,
        )


def test_template_digest_ignores_runtime_cache_files(tmp_path: Path) -> None:
    template = tmp_path / "templates"
    template.mkdir()
    (template / "tracked.j2").write_text("tracked\n", encoding="utf-8")
    expected = template_digest(template)
    cache = template / "scripts" / "__pycache__"
    cache.mkdir(parents=True)
    (cache / "runtime.cpython-312.pyc").write_bytes(b"runtime-specific")
    assert template_digest(template) == expected


def test_generation_refuses_non_empty_output(tmp_path: Path, manifest_payload: dict) -> None:
    output = tmp_path / "project"
    output.mkdir()
    (output / "owned.txt").write_text("user data")
    with pytest.raises(ValueError, match="must be empty"):
        generate_project(
            ProductManifest.model_validate(manifest_payload),
            output,
            allow_experimental=True,
        )


def test_generated_project_is_r1_batch_only(
    tmp_path: Path, manifest_payload: dict, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("aiml_scaffold.doctor.shutil.which", lambda _: "/usr/bin/tool")
    manifest_payload["product"]["display_name"] = "Example Risk"
    output = tmp_path / "project"
    generate_project(
        ProductManifest.model_validate(manifest_payload),
        output,
        allow_experimental=True,
    )
    assert (output / "infra/terraform/main.tf").is_file()
    assert (output / "mlops/azureml/deploy/batch/deployment.yml").is_file()
    assert not (output / "infra/bicep").exists()
    assert not (output / "foundry").exists()
    assert not (output / "databricks").exists()
    deployment = (output / "mlops/azureml/deploy/batch/deployment.yml").read_text()
    assert "@latest" not in deployment
    receipt = json.loads((output / "generation-receipt.json").read_text())
    assert receipt["providers"]["serving"] == "azure_ml_batch"
    source_manifest = (output / "platform/source-manifest.yaml").read_text()
    resolved_plan = json.loads((output / "platform/resolved-plan.json").read_text())
    assert "Example Risk" in source_manifest
    assert resolved_plan["provider_extensions"]["azure_ml"]["location"] == "eastus"
    assert receipt["dependency_constraints_digest"].startswith("sha256:")
    assert not (output / "product-manifest.yaml").exists()
    emitter = (output / "scripts/emit_evidence.py").read_text()
    assert "reject_sensitive_keys(item" in emitter
    doctor = doctor_project(output, "dev", cloud_checks=False)
    assert doctor["ok"] is True
    assert doctor["project"] == manifest_payload["product"]["name"]


def test_generated_terraform_uses_identity_storage_and_project_owned_compute_identity(
    tmp_path: Path, manifest_payload: dict
) -> None:
    output = tmp_path / "project"
    generate_project(
        ProductManifest.model_validate(manifest_payload),
        output,
        allow_experimental=True,
    )
    terraform = (output / "infra/terraform/main.tf").read_text(encoding="utf-8")
    assert 'storage_account_access_type   = "Identity"' in terraform
    assert 'resource "azurerm_user_assigned_identity" "compute"' in terraform
    assert 'resource "azurerm_role_assignment" "compute_storage"' in terraform
    assert 'resource "azurerm_role_assignment" "workflow_storage"' in terraform
    assert "azurerm_user_assigned_identity.compute.principal_id" in terraform
    assert "scope                            = azurerm_storage_account.this.id" in terraform
    assert 'type         = "UserAssigned"' in terraform
    assert "depends_on = [azurerm_role_assignment.compute_storage]" in terraform
    assert "workflow_evidence" not in terraform
    operational_files = [
        output / "infra/terraform/main.tf",
        *sorted((output / ".github/workflows").glob("*.yml")),
        *sorted((output / "mlops").rglob("*.yml")),
    ]
    operational_text = "\n".join(
        path.read_text(encoding="utf-8") for path in operational_files
    ).lower()
    for prohibited in ("accesskey", "accountkey", "listkeys", "connection_string", "sas_token"):
        assert prohibited not in operational_text


def test_generated_workflows_enforce_digest_bound_manual_apply(
    tmp_path: Path, manifest_payload: dict
) -> None:
    manifest_payload["policy"]["deployment_approval"] = "manual_dispatch_with_plan_digest"
    output = tmp_path / "project"
    generate_project(
        ProductManifest.model_validate(manifest_payload),
        output,
        allow_experimental=True,
    )
    plan = (output / ".github/workflows/terraform-plan.yml").read_text()
    apply = (output / ".github/workflows/terraform-apply.yml").read_text()
    smoke = (output / ".github/workflows/oidc-smoke.yml").read_text()
    artifact_script = (output / "scripts/plan_artifact.py").read_text()
    assert "actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02" in plan
    assert "approval-metadata.json" in artifact_script
    for name in (
        "r1.tfplan",
        "r1.tfplan.sha256",
        "r1-plan.sanitized.json",
        "r1-plan.sanitized.json.sha256",
        "approval-metadata.json",
        "artifact-manifest.v1.json",
    ):
        assert name in plan or name in artifact_script
    assert "terraform show -json" in plan
    assert "scripts/plan_artifact.py create" in plan
    assert "scripts/plan_artifact.py verify" in apply
    assert "reviewed_plan_digest:" in apply
    assert "reviewed_json_digest:" in apply
    assert "approval_reason:" in apply
    assert "APPLY_AUTHORIZED_ACTORS" in apply
    assert "current-state.json" in apply
    assert "apply-authorization-and-result.json" in apply
    assert "pre-plan-state.json" in plan
    assert any(
        line.strip().startswith('--state-key "') and line.rstrip().endswith("\\")
        for line in plan.splitlines()
    )
    assert "for key, backend_key in backend_keys.items()" in artifact_script
    assert "actions/download-artifact@d3f86a106a0bac45b974a628896c90dbdf5c8093" in apply
    assert "terraform plan" not in apply
    assert "approved-plan/r1.tfplan" in apply
    assert "workflow_dispatch:" in smoke
    assert "az account get-access-token" in smoke
    assert "terraform apply" not in smoke
    for workflow in (plan, apply):
        assert 'ARM_USE_OIDC: "true"' in workflow
        assert 'ARM_USE_AZUREAD: "true"' in workflow
        assert "ARM_CLIENT_ID: ${{ secrets.AZURE_CLIENT_ID }}" in workflow
        assert "ARM_TENANT_ID: ${{ secrets.AZURE_TENANT_ID }}" in workflow
        assert "ARM_SUBSCRIPTION_ID: ${{ secrets.AZURE_SUBSCRIPTION_ID }}" in workflow
    for workflow in (plan, apply, smoke):
        assert "pip install -c constraints.txt pyyaml" in workflow
        assert "pyyaml==6.0.3" not in workflow


def test_plan_artifact_sanitization_and_integrity_contract(
    tmp_path: Path, manifest_payload: dict
) -> None:
    output = tmp_path / "project"
    generate_project(
        ProductManifest.model_validate(manifest_payload),
        output,
        allow_experimental=True,
    )
    module = _load_module(output / "scripts/plan_artifact.py")
    raw = {
        "resource_changes": [
            {
                "change": {
                    "actions": ["create"],
                    "after": {"name": "safe", "client_secret": "credential"},
                    "after_sensitive": {"client_secret": True},
                }
            }
        ]
    }
    sanitized = module._sanitize(raw)
    assert sanitized["resource_changes"][0]["change"]["after"]["client_secret"] == module.REDACTED
    assert module._action_summary(sanitized)["create"] == 1
    module._assert_no_credentials(sanitized)
    with pytest.raises(ValueError, match="credential-bearing URI"):
        module._assert_no_credentials("https://example.invalid/blob?sig=secret")
    with pytest.raises(ValueError, match="unredacted sensitive field"):
        module._assert_no_credentials({"primary_access_key": "secret"})

    artifact = tmp_path / "artifact"
    artifact.mkdir()
    (artifact / "r1.tfplan").write_bytes(b"binary-plan")
    module._write_json(artifact / "r1-plan.sanitized.json", sanitized)
    plan_digest = module._sha256(artifact / "r1.tfplan")
    json_digest = module._sha256(artifact / "r1-plan.sanitized.json")
    module._write_digest(artifact / "r1.tfplan.sha256", plan_digest, "r1.tfplan")
    module._write_digest(
        artifact / "r1-plan.sanitized.json.sha256",
        json_digest,
        "r1-plan.sanitized.json",
    )
    approval = {
        "approval_contract_version": "1.0",
        "source_commit": "a" * 40,
        "platform_source_commit": "c" * 40,
        "platform_package_digest": "sha256:" + "d" * 64,
        "generation_id": "sha256:" + "b" * 64,
        "target_environment": "dev",
        "terraform_plan_digest": plan_digest,
        "sanitized_plan_digest": json_digest,
        "plan_run_id": "123",
        "plan_run_attempt": "1",
        "plan_requested_by": "operator",
    }
    module._write_json(artifact / "approval-metadata.json", approval)
    created_at = datetime.now(UTC)
    state_snapshot = tmp_path / "state.json"
    module._write_json(state_snapshot, {"state_absent": True})
    state_identity = module._state_identity(state_snapshot)
    manifest = {
        "artifact_manifest_schema_version": "1.0",
        "created_at": created_at.isoformat(),
        "expires_at": (created_at + timedelta(days=30)).isoformat(),
        "maximum_plan_age_hours": 720,
        "expected_files": sorted(module.EXPECTED_FILES),
        "source_commit": approval["source_commit"],
        "platform_source_commit": approval["platform_source_commit"],
        "platform_package_digest": approval["platform_package_digest"],
        "generation_id": approval["generation_id"],
        "tenant_id": "00000000-0000-0000-0000-000000000000",
        "subscription_id": "11111111-1111-1111-1111-111111111111",
        "target_environment": "dev",
        "plan_run_id": "123",
        "plan_run_attempt": "1",
        "terraform_plan_digest": plan_digest,
        "sanitized_plan_digest": json_digest,
        "action_summary": module._action_summary(sanitized),
        "backend": {
            "state": state_identity
        },
    }
    manifest["files"] = {
        name: module._sha256(artifact / name)
        for name in sorted(module.EXPECTED_FILES - {"artifact-manifest.v1.json"})
    }
    module._write_json(artifact / "artifact-manifest.v1.json", manifest)
    module.verify_artifact(
        artifact,
        expected_run_id="123",
        expected_run_attempt="1",
        expected_environment="dev",
        reviewed_plan_digest=plan_digest,
        reviewed_json_digest=json_digest,
        expected_tenant_id=manifest["tenant_id"],
        expected_subscription_id=manifest["subscription_id"],
        current_state_snapshot=state_snapshot,
    )

    module._write_json(state_snapshot, {"lineage": "changed", "serial": 1})
    with pytest.raises(ValueError, match="backend_state_unchanged"):
        module.verify_artifact(artifact, current_state_snapshot=state_snapshot)

    with pytest.raises(ValueError, match="not_expired"):
        module.verify_artifact(artifact, now=created_at + timedelta(days=31))

    extra = tmp_path / "extra"
    shutil.copytree(artifact, extra)
    (extra / "unexpected.txt").write_text("unexpected", encoding="utf-8")
    with pytest.raises(ValueError, match="contents do not match"):
        module.verify_artifact(extra)

    conflicting = tmp_path / "conflicting"
    shutil.copytree(artifact, conflicting)
    conflicting_manifest = json.loads(
        (conflicting / "artifact-manifest.v1.json").read_text(encoding="utf-8")
    )
    conflicting_manifest["action_summary"]["create"] = 0
    module._write_json(conflicting / "artifact-manifest.v1.json", conflicting_manifest)
    with pytest.raises(ValueError, match="manifest_action_summary"):
        module.verify_artifact(conflicting)

    duplicate = tmp_path / "duplicate"
    shutil.copytree(artifact, duplicate)
    (duplicate / "approval-metadata.json").write_text(
        '{"plan_run_id":"123","plan_run_id":"456"}\n', encoding="utf-8"
    )
    duplicate_manifest = json.loads(
        (duplicate / "artifact-manifest.v1.json").read_text(encoding="utf-8")
    )
    duplicate_manifest["files"]["approval-metadata.json"] = module._sha256(
        duplicate / "approval-metadata.json"
    )
    module._write_json(duplicate / "artifact-manifest.v1.json", duplicate_manifest)
    with pytest.raises(ValueError, match="duplicate key"):
        module.verify_artifact(duplicate)


def test_generated_receipt_remains_valid_after_git_metadata_is_created(
    tmp_path: Path, manifest_payload: dict
) -> None:
    output = tmp_path / "project"
    _, receipt = generate_project(
        ProductManifest.model_validate(manifest_payload),
        output,
        allow_experimental=True,
    )
    git_metadata = output / ".git"
    git_metadata.mkdir()
    (git_metadata / "HEAD").write_text("ref: refs/heads/main\n", encoding="utf-8")
    assert verify_generation(output)["generation_id"] == receipt["generation_id"]


def test_modified_generated_tree_fails_receipt_check(
    tmp_path: Path, manifest_payload: dict
) -> None:
    output = tmp_path / "project"
    generate_project(
        ProductManifest.model_validate(manifest_payload),
        output,
        allow_experimental=True,
    )
    (output / "README.md").write_text("modified")
    with pytest.raises(ValueError, match="digest mismatch"):
        verify_generation(output)


def test_modified_provenance_fails_specific_digest_check(
    tmp_path: Path, manifest_payload: dict
) -> None:
    output = tmp_path / "project"
    generate_project(
        ProductManifest.model_validate(manifest_payload),
        output,
        allow_experimental=True,
    )
    receipt_path = output / "generation-receipt.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    source = output / "platform/source-manifest.yaml"
    source_payload = yaml.safe_load(source.read_text(encoding="utf-8"))
    source_payload["product"]["owner"] = "changed@example.com"
    source.write_text(yaml.safe_dump(source_payload), encoding="utf-8")
    receipt["generated_files_digest"] = generated_files_digest(output)
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    with pytest.raises(ValueError, match="manifest_digest mismatch"):
        verify_generation(output)


def test_normalized_provider_extension_changes_generation_identity(
    tmp_path: Path, manifest_payload: dict
) -> None:
    first_manifest = ProductManifest.model_validate(manifest_payload)
    manifest_payload["provider_extensions"]["azure_ml"]["compute_size"] = "Standard_D8s_v5"
    second_manifest = ProductManifest.model_validate(manifest_payload)
    _, first = generate_project(first_manifest, tmp_path / "first", allow_experimental=True)
    _, second = generate_project(second_manifest, tmp_path / "second", allow_experimental=True)
    assert first["generation_id"] != second["generation_id"]
    assert first["resolved_plan_digest"] != second["resolved_plan_digest"]


def test_source_manifest_excludes_unsupplied_defaults(
    tmp_path: Path, manifest_payload: dict
) -> None:
    manifest_payload.pop("provider_extensions")
    manifest_payload.pop("environments")
    output = tmp_path / "project"
    generate_project(
        ProductManifest.model_validate(manifest_payload),
        output,
        allow_experimental=True,
    )
    source = yaml.safe_load((output / "platform/source-manifest.yaml").read_text(encoding="utf-8"))
    resolved = json.loads((output / "platform/resolved-plan.json").read_text(encoding="utf-8"))
    assert "provider_extensions" not in source
    assert "environments" not in source
    assert resolved["environment_topology"]["dev"]["resource_group"] == "rg-example-risk-dev"
