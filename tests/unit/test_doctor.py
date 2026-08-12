from __future__ import annotations

import json
from pathlib import Path

import pytest

import aiml_scaffold.doctor as doctor_module
from aiml_scaffold.generator import generate_project
from platform_core.contracts.product_manifest import ProductManifest

TENANT_ID = "00000000-0000-0000-0000-000000000001"
SUBSCRIPTION_ID = "00000000-0000-0000-0000-000000000000"
CLIENT_ID = "10000000-0000-0000-0000-000000000001"
OBJECT_ID = "20000000-0000-0000-0000-000000000001"
GROUP_ID = f"/subscriptions/{SUBSCRIPTION_ID}/resourceGroups/rg-example-risk-dev"


@pytest.fixture
def generated_project(tmp_path: Path, manifest_payload: dict) -> Path:
    project = tmp_path / "project"
    generate_project(
        ProductManifest.model_validate(manifest_payload),
        project,
        allow_experimental=True,
    )
    return project


def _check(result: dict, name: str) -> dict:
    return next(item for item in result["checks"] if item["check"] == name)


def _successful_azure_response(command: list[str]) -> tuple[bool, str]:
    joined = " ".join(command)
    if command[1:3] == ["account", "show"]:
        return True, json.dumps(
            {
                "id": SUBSCRIPTION_ID,
                "tenantId": TENANT_ID,
                "user": {"name": CLIENT_ID, "type": "servicePrincipal"},
            }
        )
    if command[1:3] == ["group", "show"]:
        return True, json.dumps({"id": GROUP_ID})
    if command[1:4] == ["storage", "account", "show"]:
        return True, json.dumps({"allowSharedKeyAccess": False})
    if command[1:4] == ["storage", "container-rm", "show"]:
        return True, "{}"
    if command[1:4] == ["storage", "blob", "list"]:
        return True, "[]"
    if command[1:4] == ["ad", "app", "show"]:
        return True, json.dumps({"appId": CLIENT_ID, "id": "application-object-id"})
    if command[1:4] == ["ad", "sp", "show"]:
        return True, json.dumps({"appId": CLIENT_ID, "id": OBJECT_ID})
    if command[1:5] == ["ad", "app", "federated-credential", "list"]:
        return True, json.dumps(
            [
                {
                    "issuer": "https://token.actions.githubusercontent.com",
                    "subject": "repo:example/example-risk:environment:dev",
                    "audiences": ["api://AzureADTokenExchange"],
                }
            ]
        )
    if command[1:4] == ["role", "assignment", "list"] and "--scope" in command:
        return True, json.dumps(
            [
                {"roleDefinitionName": "Contributor", "scope": GROUP_ID},
                {"roleDefinitionName": "User Access Administrator", "scope": GROUP_ID},
            ]
        )
    if command[1:4] == ["role", "assignment", "list"] and "--all" in command:
        return True, "[]"
    if command[1:3] == ["vm", "list-skus"]:
        return True, json.dumps(
            [
                {
                    "name": "Standard_D4s_v5",
                    "family": "standardDSv5Family",
                    "restrictions": [],
                    "capabilities": [{"name": "vCPUs", "value": "4"}],
                }
            ]
        )
    if command[1:3] == ["vm", "list-usage"]:
        return True, json.dumps(
            [
                {
                    "name": {"value": "standardDSv5Family"},
                    "currentValue": 0,
                    "limit": 100,
                }
            ]
        )
    raise AssertionError(f"unexpected read-only Azure command: {joined}")


def _configure_authenticated_doctor(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AZURE_CLIENT_ID", CLIENT_ID)
    monkeypatch.setenv("AZURE_CLIENT_OBJECT_ID", OBJECT_ID)
    monkeypatch.setattr(doctor_module.shutil, "which", lambda _: "/usr/bin/tool")
    monkeypatch.setattr(doctor_module, "_run_read_only", _successful_azure_response)


def test_offline_doctor_uses_not_exercised_for_cloud_checks(
    generated_project: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(doctor_module.shutil, "which", lambda _: "/usr/bin/tool")
    result = doctor_module.doctor_project(
        generated_project, "dev", cloud_checks=False
    )
    assert result["overall_status"] == "passed"
    assert _check(result, "azure_context_match")["status"] == "not_exercised"
    assert _check(result, "oidc_token_exchange")["status"] == "not_exercised"


def test_authenticated_doctor_reports_each_preflight_boundary(
    generated_project: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _configure_authenticated_doctor(monkeypatch)
    result = doctor_module.doctor_project(generated_project, "dev")
    assert result["overall_status"] == "passed"
    for name in (
        "azure_context_match",
        "backend_management_plane_visibility",
        "backend_container_exists",
        "backend_data_plane_read",
        "backend_shared_key_posture",
        "oidc_application_principal_relationship",
        "oidc_federated_credential",
        "environment_scoped_rbac",
        "compute_sku_availability",
        "compute_quota_sufficiency",
        "active_identity_match",
    ):
        assert _check(result, name)["status"] == "passed"
    assert _check(result, "backend_state_write_and_lock")["status"] == "not_exercised"
    assert _check(result, "oidc_token_exchange")["status"] == "not_exercised"


def test_authenticated_doctor_requests_subscription_aware_full_sku_metadata(
    generated_project: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _configure_authenticated_doctor(monkeypatch)
    observed: list[list[str]] = []

    def record_commands(command: list[str]) -> tuple[bool, str]:
        observed.append(command)
        return _successful_azure_response(command)

    monkeypatch.setattr(doctor_module, "_run_read_only", record_commands)
    result = doctor_module.doctor_project(generated_project, "dev")
    assert result["overall_status"] == "passed"
    sku_command = next(command for command in observed if command[1:3] == ["vm", "list-skus"])
    assert "--all" in sku_command
    assert "--resource-type" not in sku_command


def test_subscription_restricted_sku_fails_even_when_quota_exists(
    generated_project: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _configure_authenticated_doctor(monkeypatch)

    def restricted_sku(command: list[str]) -> tuple[bool, str]:
        if command[1:3] == ["vm", "list-skus"]:
            return True, json.dumps(
                [
                    {
                        "name": "Standard_D4s_v5",
                        "family": "standardDSv5Family",
                        "restrictions": [
                            {
                                "reasonCode": "NotAvailableForSubscription",
                                "type": "Location",
                                "values": ["eastus"],
                            }
                        ],
                        "capabilities": [{"name": "vCPUs", "value": "4"}],
                    }
                ]
            )
        return _successful_azure_response(command)

    monkeypatch.setattr(doctor_module, "_run_read_only", restricted_sku)
    result = doctor_module.doctor_project(generated_project, "dev")
    sku_check = _check(result, "compute_sku_availability")
    assert sku_check["status"] == "failed"
    assert sku_check["restrictions"][0]["reasonCode"] == "NotAvailableForSubscription"
    assert _check(result, "compute_quota_sufficiency")["status"] == "passed"


def test_context_mismatch_is_not_collapsed_into_other_checks(
    generated_project: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _configure_authenticated_doctor(monkeypatch)

    def mismatched_context(command: list[str]) -> tuple[bool, str]:
        if command[1:3] == ["account", "show"]:
            return True, json.dumps(
                {
                    "id": "30000000-0000-0000-0000-000000000001",
                    "tenantId": TENANT_ID,
                    "user": {"name": CLIENT_ID, "type": "servicePrincipal"},
                }
            )
        return _successful_azure_response(command)

    monkeypatch.setattr(doctor_module, "_run_read_only", mismatched_context)
    result = doctor_module.doctor_project(generated_project, "dev")
    assert result["overall_status"] == "failed"
    assert _check(result, "azure_context_match")["status"] == "failed"
    assert _check(result, "backend_management_plane_visibility")["status"] == "passed"


def test_backend_data_plane_failure_is_reported_separately(
    generated_project: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _configure_authenticated_doctor(monkeypatch)

    def no_blob_access(command: list[str]) -> tuple[bool, str]:
        if command[1:4] == ["storage", "blob", "list"]:
            return False, "authorization failed"
        return _successful_azure_response(command)

    monkeypatch.setattr(doctor_module, "_run_read_only", no_blob_access)
    result = doctor_module.doctor_project(generated_project, "dev")
    assert _check(result, "backend_container_exists")["status"] == "passed"
    assert _check(result, "backend_data_plane_read")["status"] == "failed"


def test_insufficient_quota_fails_without_changing_sku_result(
    generated_project: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _configure_authenticated_doctor(monkeypatch)

    def insufficient_quota(command: list[str]) -> tuple[bool, str]:
        if command[1:3] == ["vm", "list-usage"]:
            return True, json.dumps(
                [
                    {
                        "name": {"value": "standardDSv5Family"},
                        "currentValue": 8,
                        "limit": 8,
                    }
                ]
            )
        return _successful_azure_response(command)

    monkeypatch.setattr(doctor_module, "_run_read_only", insufficient_quota)
    result = doctor_module.doctor_project(generated_project, "dev")
    assert _check(result, "compute_sku_availability")["status"] == "passed"
    assert _check(result, "compute_quota_sufficiency")["status"] == "failed"


def test_active_identity_difference_is_a_warning(
    generated_project: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _configure_authenticated_doctor(monkeypatch)

    def local_user_context(command: list[str]) -> tuple[bool, str]:
        if command[1:3] == ["account", "show"]:
            return True, json.dumps(
                {
                    "id": SUBSCRIPTION_ID,
                    "tenantId": TENANT_ID,
                    "user": {"name": "developer@example.com", "type": "user"},
                }
            )
        return _successful_azure_response(command)

    monkeypatch.setattr(doctor_module, "_run_read_only", local_user_context)
    result = doctor_module.doctor_project(generated_project, "dev")
    assert result["overall_status"] == "warning"
    assert _check(result, "active_identity_match")["status"] == "warning"
    assert _check(result, "oidc_token_exchange")["status"] == "not_exercised"


def test_receipt_tampering_stops_before_authenticated_checks(
    generated_project: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    receipt_path = generated_project / "generation-receipt.json"
    receipt_path.write_text("{}\n", encoding="utf-8")
    monkeypatch.setattr(
        doctor_module,
        "_run_read_only",
        lambda _: pytest.fail("cloud checks must not run before receipt verification"),
    )
    with pytest.raises(ValueError, match="receipt"):
        doctor_module.doctor_project(generated_project, "dev")
