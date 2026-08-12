from __future__ import annotations

import json
from pathlib import Path

import yaml
from jinja2 import TemplateNotFound

from aiml_scaffold import cli
from aiml_scaffold.generator import generate_project
from platform_core.contracts.product_manifest import ProductManifest


def _write_manifest(path: Path, manifest_payload: dict) -> None:
    path.write_text(yaml.safe_dump(manifest_payload), encoding="utf-8")


def test_validate_reports_maturity_authorization(
    tmp_path: Path, manifest_payload: dict, capsys
) -> None:
    manifest = tmp_path / "manifest.yaml"
    _write_manifest(manifest, manifest_payload)
    assert cli.main(["validate", str(manifest), "--allow-experimental"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert payload["maturity"] == {
        "release_status": "preview",
        "manifest_policy": "allow_preview",
        "cli_override_supplied": True,
        "authorization_result": "allowed",
        "remaining_evidence_boundary": "dev_live_pending",
    }


def test_plan_contains_maturity_report(
    tmp_path: Path, manifest_payload: dict, capsys
) -> None:
    manifest = tmp_path / "manifest.yaml"
    _write_manifest(manifest, manifest_payload)
    assert cli.main(["plan", str(manifest), "--allow-experimental"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["maturity_report"]["release_status"] == "preview"
    assert payload["maturity_report"]["cli_override_supplied"] is True


def test_missing_manifest_returns_stable_json(capsys) -> None:
    assert cli.main(["validate", "/not-present/manifest.yaml"]) == 3
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is False
    assert payload["command"] == "validate"
    assert payload["error"]["code"] == "MANIFEST_NOT_FOUND"
    assert "Traceback" not in json.dumps(payload)


def test_malformed_manifest_returns_stable_json(tmp_path: Path, capsys) -> None:
    manifest = tmp_path / "manifest.yaml"
    manifest.write_text("capabilities: [", encoding="utf-8")
    assert cli.main(["validate", str(manifest)]) == 4
    payload = json.loads(capsys.readouterr().out)
    assert payload["error"]["code"] == "DOCUMENT_FORMAT_INVALID"


def test_output_permission_failure_returns_stable_json(
    tmp_path: Path, manifest_payload: dict, capsys, monkeypatch
) -> None:
    manifest = tmp_path / "manifest.yaml"
    _write_manifest(manifest, manifest_payload)

    def denied(*args, **kwargs):
        raise PermissionError("internal path details")

    monkeypatch.setattr(cli, "generate_project", denied)
    output = tmp_path / "output"
    assert (
        cli.main(
            [
                "generate",
                str(manifest),
                "--output",
                str(output),
                "--allow-experimental",
            ]
        )
        == 3
    )
    payload = json.loads(capsys.readouterr().out)
    assert payload["error"]["code"] == "OUTPUT_PERMISSION_DENIED"
    assert "internal path details" not in json.dumps(payload)


def test_output_file_returns_stable_path_error(
    tmp_path: Path, manifest_payload: dict, capsys
) -> None:
    manifest = tmp_path / "manifest.yaml"
    _write_manifest(manifest, manifest_payload)
    output = tmp_path / "output"
    output.write_text("owned", encoding="utf-8")
    assert (
        cli.main(
            [
                "generate",
                str(manifest),
                "--output",
                str(output),
                "--allow-experimental",
            ]
        )
        == 3
    )
    payload = json.loads(capsys.readouterr().out)
    assert payload["error"]["code"] == "PATH_TYPE_INVALID"


def test_missing_template_content_returns_stable_json(
    tmp_path: Path, manifest_payload: dict, capsys, monkeypatch
) -> None:
    manifest = tmp_path / "manifest.yaml"
    _write_manifest(manifest, manifest_payload)

    def missing(*args, **kwargs):
        raise TemplateNotFound("internal-template-path")

    monkeypatch.setattr(cli, "generate_project", missing)
    assert (
        cli.main(
            [
                "generate",
                str(manifest),
                "--output",
                str(tmp_path / "output"),
                "--allow-experimental",
            ]
        )
        == 4
    )
    payload = json.loads(capsys.readouterr().out)
    assert payload["error"]["code"] == "TEMPLATE_CONTENT_MISSING"
    assert "internal-template-path" not in json.dumps(payload)


def test_malformed_receipt_returns_stable_json(
    tmp_path: Path, manifest_payload: dict, capsys
) -> None:
    project = tmp_path / "project"
    generate_project(
        ProductManifest.model_validate(manifest_payload),
        project,
        allow_experimental=True,
    )
    (project / "generation-receipt.json").write_text("{", encoding="utf-8")
    assert cli.main(["doctor", str(project), "--no-cloud"]) == 4
    payload = json.loads(capsys.readouterr().out)
    assert payload["error"]["code"] == "DOCUMENT_FORMAT_INVALID"
