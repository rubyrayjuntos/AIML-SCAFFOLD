from __future__ import annotations

import json
from pathlib import Path

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


def test_generation_is_byte_stable(tmp_path: Path, manifest_payload: dict) -> None:
    manifest = ProductManifest.model_validate(manifest_payload)
    first = tmp_path / "first"
    second = tmp_path / "second"
    _, first_receipt = generate_project(
        manifest, first, allow_experimental=True
    )
    _, second_receipt = generate_project(
        manifest, second, allow_experimental=True
    )
    assert _tree(first) == _tree(second)
    assert first_receipt == second_receipt
    assert verify_generation(first)["generation_id"] == first_receipt["generation_id"]


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


def test_generated_workflows_enforce_digest_bound_manual_apply(
    tmp_path: Path, manifest_payload: dict
) -> None:
    manifest_payload["policy"][
        "deployment_approval"
    ] = "manual_dispatch_with_plan_digest"
    output = tmp_path / "project"
    generate_project(
        ProductManifest.model_validate(manifest_payload),
        output,
        allow_experimental=True,
    )
    plan = (output / ".github/workflows/terraform-plan.yml").read_text()
    apply = (output / ".github/workflows/terraform-apply.yml").read_text()
    smoke = (output / ".github/workflows/oidc-smoke.yml").read_text()
    assert "actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02" in plan
    assert "approval-metadata.json" in plan
    assert "reviewed_plan_digest:" in apply
    assert (
        "actions/download-artifact@d3f86a106a0bac45b974a628896c90dbdf5c8093"
        in apply
    )
    assert "terraform plan" not in apply
    assert "approved-plan/r1.tfplan" in apply
    assert "workflow_dispatch:" in smoke
    assert "az account get-access-token" in smoke
    assert "terraform apply" not in smoke
    for workflow in (plan, apply, smoke):
        assert "pip install -c constraints.txt pyyaml" in workflow
        assert "pyyaml==6.0.3" not in workflow


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
    _, first = generate_project(
        first_manifest, tmp_path / "first", allow_experimental=True
    )
    _, second = generate_project(
        second_manifest, tmp_path / "second", allow_experimental=True
    )
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
    source = yaml.safe_load(
        (output / "platform/source-manifest.yaml").read_text(encoding="utf-8")
    )
    resolved = json.loads(
        (output / "platform/resolved-plan.json").read_text(encoding="utf-8")
    )
    assert "provider_extensions" not in source
    assert "environments" not in source
    assert resolved["environment_topology"]["dev"]["resource_group"] == "rg-example-risk-dev"
