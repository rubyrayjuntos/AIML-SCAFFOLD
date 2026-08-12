from __future__ import annotations

import json
import os
import shutil
import subprocess
from enum import StrEnum
from pathlib import Path
from typing import Any

import yaml

from aiml_scaffold.generator import verify_generation


class CheckStatus(StrEnum):
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    NOT_EXERCISED = "not_exercised"
    NOT_APPLICABLE = "not_applicable"


_CLOUD_CHECKS = (
    "azure_context_match",
    "active_identity_match",
    "environment_resource_group",
    "backend_subscription_policy",
    "backend_management_plane_visibility",
    "backend_container_exists",
    "backend_data_plane_read",
    "backend_state_write_and_lock",
    "backend_shared_key_posture",
    "oidc_application_principal_relationship",
    "oidc_federated_credential",
    "environment_scoped_rbac",
    "subscription_owner_absent",
    "oidc_token_exchange",
    "compute_sku_availability",
    "compute_quota_sufficiency",
)


def _run_read_only(command: list[str]) -> tuple[bool, str]:
    try:
        result = subprocess.run(command, check=False, capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, str(exc)
    output = (result.stdout or result.stderr).strip()
    return result.returncode == 0, output


def _check(
    name: str,
    status: CheckStatus,
    message: str,
    **details: Any,
) -> dict[str, Any]:
    return {
        "check": name,
        "status": status.value,
        "message": message,
        **details,
    }


def _json(value: str) -> Any:
    return json.loads(value) if value else None


def _arm_leaf(resource_id: str) -> str:
    return resource_id.rstrip("/").split("/")[-1]


def _arm_resource_group(resource_id: str) -> str:
    parts = resource_id.rstrip("/").split("/")
    return parts[parts.index("resourceGroups") + 1]


def _not_exercised_cloud_checks() -> list[dict[str, Any]]:
    checks = []
    for name in _CLOUD_CHECKS:
        message = "Authenticated cloud checks were not requested."
        if name == "oidc_token_exchange":
            message = "Only a GitHub Actions workflow can exercise OIDC token exchange."
        checks.append(_check(name, CheckStatus.NOT_EXERCISED, message))
    return checks


def _overall_status(checks: list[dict[str, Any]]) -> str:
    statuses = {check["status"] for check in checks}
    if CheckStatus.FAILED.value in statuses:
        return CheckStatus.FAILED.value
    if CheckStatus.WARNING.value in statuses:
        return CheckStatus.WARNING.value
    return CheckStatus.PASSED.value


def _cloud_checks(
    *,
    project: Path,
    manifest: dict[str, Any],
    plan: dict[str, Any],
    environment: str,
) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    azure_context = plan["azure_context"]
    deployment_subscription = azure_context["deployment_subscription_id"]
    backend_subscription = azure_context["backend_subscription_id"]
    expected_tenant = azure_context["expected_tenant_id"]
    backend = manifest["shared_resources"]["terraform_backend"]
    storage_id = backend["storage_account_id"]
    storage_name = _arm_leaf(storage_id)
    backend_resource_group = _arm_resource_group(storage_id)
    container_name = backend["container_name"]
    config = yaml.safe_load(
        (project / "config" / f"{environment}.yaml").read_text(encoding="utf-8")
    )

    account_ok, account_output = _run_read_only(
        ["az", "account", "show", "--output", "json"]
    )
    account = _json(account_output) if account_ok else None
    context_matches = bool(
        account
        and str(account.get("id", "")).lower() == deployment_subscription
        and str(account.get("tenantId", "")).lower() == expected_tenant
    )
    checks.append(
        _check(
            "azure_context_match",
            CheckStatus.PASSED if context_matches else CheckStatus.FAILED,
            (
                "Active Azure tenant and subscription match the resolved plan."
                if context_matches
                else "Active Azure tenant or subscription does not match the resolved plan."
            ),
            expected_tenant_id=expected_tenant,
            expected_subscription_id=deployment_subscription,
            active_tenant_id=(str(account.get("tenantId", "")).lower() if account else None),
            active_subscription_id=(str(account.get("id", "")).lower() if account else None),
        )
    )

    client_env = azure_context["deployment_identity_client_id_environment_variable"]
    object_env = azure_context["deployment_identity_object_id_environment_variable"]
    client_id = os.getenv(client_env)
    object_id = os.getenv(object_env)
    active_name = str((account or {}).get("user", {}).get("name", ""))
    active_type = str((account or {}).get("user", {}).get("type", "unknown"))
    intended_is_active = bool(client_id and active_name.lower() == client_id.lower())
    checks.append(
        _check(
            "active_identity_match",
            CheckStatus.PASSED if intended_is_active else CheckStatus.WARNING,
            (
                "Active CLI identity is the intended deployment identity."
                if intended_is_active
                else "Active CLI identity differs from the intended GitHub deployment identity."
            ),
            active_identity_type=active_type,
            intended_identity_configured=bool(client_id and object_id),
        )
    )

    group_ok, group_output = _run_read_only(
        [
            "az",
            "group",
            "show",
            "--name",
            config["resource_group"],
            "--subscription",
            deployment_subscription,
            "--output",
            "json",
        ]
    )
    group = _json(group_output) if group_ok else None
    checks.append(
        _check(
            "environment_resource_group",
            CheckStatus.PASSED if group_ok else CheckStatus.FAILED,
            (
                "Environment resource group is visible."
                if group_ok
                else "Environment resource group is unavailable."
            ),
            resource_group=config["resource_group"],
        )
    )

    cross_subscription = azure_context["cross_subscription_backend"]
    cross_allowed = azure_context["cross_subscription_backend_allowed"]
    checks.append(
        _check(
            "backend_subscription_policy",
            CheckStatus.PASSED,
            (
                "Cross-subscription backend is explicitly allowed by policy."
                if cross_subscription
                else "Backend and deployment use the same subscription."
            ),
            deployment_subscription_id=deployment_subscription,
            backend_subscription_id=backend_subscription,
            cross_subscription=cross_subscription,
            cross_subscription_allowed=cross_allowed,
        )
    )

    storage_ok, storage_output = _run_read_only(
        ["az", "storage", "account", "show", "--ids", storage_id, "--output", "json"]
    )
    storage = _json(storage_output) if storage_ok else None
    checks.append(
        _check(
            "backend_management_plane_visibility",
            CheckStatus.PASSED if storage_ok else CheckStatus.FAILED,
            (
                "Backend storage account is visible."
                if storage_ok
                else "Backend storage account is unavailable."
            ),
            storage_account=storage_name,
        )
    )

    container_ok, _ = _run_read_only(
        [
            "az",
            "storage",
            "container-rm",
            "show",
            "--storage-account",
            storage_name,
            "--resource-group",
            backend_resource_group,
            "--name",
            container_name,
            "--subscription",
            backend_subscription,
            "--output",
            "json",
        ]
    )
    checks.append(
        _check(
            "backend_container_exists",
            CheckStatus.PASSED if container_ok else CheckStatus.FAILED,
            (
                "Terraform state container exists."
                if container_ok
                else "Terraform state container was not found."
            ),
            container=container_name,
        )
    )

    blob_read_ok, _ = _run_read_only(
        [
            "az",
            "storage",
            "blob",
            "list",
            "--account-name",
            storage_name,
            "--container-name",
            container_name,
            "--auth-mode",
            "login",
            "--num-results",
            "1",
            "--subscription",
            backend_subscription,
            "--output",
            "json",
        ]
    )
    checks.append(
        _check(
            "backend_data_plane_read",
            CheckStatus.PASSED if blob_read_ok else CheckStatus.FAILED,
            (
                "Active identity can list state blobs through Entra authentication."
                if blob_read_ok
                else "Active identity cannot list state blobs through Entra authentication."
            ),
        )
    )
    checks.append(
        _check(
            "backend_state_write_and_lock",
            CheckStatus.NOT_EXERCISED,
            "State write and lock acquisition are deferred to the reviewed Terraform plan.",
        )
    )
    shared_key_enabled = (storage or {}).get("allowSharedKeyAccess")
    shared_key_status = (
        CheckStatus.PASSED if shared_key_enabled is False else CheckStatus.WARNING
    )
    checks.append(
        _check(
            "backend_shared_key_posture",
            shared_key_status,
            (
                "Backend shared-key access is disabled."
                if shared_key_enabled is False
                else "Backend shared-key access is enabled or could not be confirmed disabled."
            ),
            shared_key_access_enabled=shared_key_enabled,
        )
    )

    app = None
    principal = None
    relationship_ok = False
    if client_id and object_id:
        app_ok, app_output = _run_read_only(
            ["az", "ad", "app", "show", "--id", client_id, "--output", "json"]
        )
        principal_ok, principal_output = _run_read_only(
            ["az", "ad", "sp", "show", "--id", client_id, "--output", "json"]
        )
        app = _json(app_output) if app_ok else None
        principal = _json(principal_output) if principal_ok else None
        relationship_ok = bool(
            app
            and principal
            and str(app.get("appId", "")).lower() == client_id.lower()
            and str(principal.get("appId", "")).lower() == client_id.lower()
            and str(principal.get("id", "")).lower() == object_id.lower()
        )
    checks.append(
        _check(
            "oidc_application_principal_relationship",
            CheckStatus.PASSED if relationship_ok else CheckStatus.FAILED,
            (
                "OIDC application and service principal IDs are consistent."
                if relationship_ok
                else "OIDC application and service principal relationship could not be verified."
            ),
            client_id_configuration=client_env,
            object_id_configuration=object_env,
        )
    )

    federated_ok = False
    if relationship_ok and app:
        credential_ok, credential_output = _run_read_only(
            [
                "az",
                "ad",
                "app",
                "federated-credential",
                "list",
                "--id",
                app["id"],
                "--output",
                "json",
            ]
        )
        credentials = _json(credential_output) if credential_ok else []
        federated_ok = any(
            credential.get("issuer") == azure_context["oidc_issuer"]
            and credential.get("subject") == azure_context["oidc_subject"]
            and credential.get("audiences") == [azure_context["oidc_audience"]]
            for credential in credentials or []
        )
    checks.append(
        _check(
            "oidc_federated_credential",
            CheckStatus.PASSED if federated_ok else CheckStatus.FAILED,
            (
                "Federated credential issuer, subject, and audience match intent."
                if federated_ok
                else "Expected federated credential was not verified."
            ),
            expected_issuer=azure_context["oidc_issuer"],
            expected_subject=azure_context["oidc_subject"],
            expected_audience=azure_context["oidc_audience"],
        )
    )

    roles: set[str] = set()
    exact_scope_roles: set[str] = set()
    if object_id and group:
        roles_ok, roles_output = _run_read_only(
            [
                "az",
                "role",
                "assignment",
                "list",
                "--assignee-object-id",
                object_id,
                "--scope",
                group["id"],
                "--include-inherited",
                "--output",
                "json",
            ]
        )
        assignments = _json(roles_output) if roles_ok else []
        roles = {
            item.get("roleDefinitionName")
            for item in assignments or []
            if item.get("roleDefinitionName")
        }
        exact_scope_roles = {
            item.get("roleDefinitionName")
            for item in assignments or []
            if str(item.get("scope", "")).lower() == str(group["id"]).lower()
            and item.get("roleDefinitionName")
        }
    required_roles = {"Contributor", "User Access Administrator"}
    rbac_ok = required_roles.issubset(exact_scope_roles)
    checks.append(
        _check(
            "environment_scoped_rbac",
            CheckStatus.PASSED if rbac_ok else CheckStatus.FAILED,
            (
                "Deployment identity has environment-scoped Contributor and "
                "User Access Administrator."
                if rbac_ok
                else "Required environment-scoped deployment roles were not verified."
            ),
            exact_scope_roles=sorted(exact_scope_roles),
            inherited_roles=sorted(roles - exact_scope_roles),
            rationale=(
                "User Access Administrator is required because generated Terraform creates the "
                "evidence-container role assignment."
            ),
        )
    )

    subscription_owner = False
    if object_id:
        all_roles_ok, all_roles_output = _run_read_only(
            [
                "az",
                "role",
                "assignment",
                "list",
                "--assignee-object-id",
                object_id,
                "--all",
                "--subscription",
                deployment_subscription,
                "--output",
                "json",
            ]
        )
        all_assignments = _json(all_roles_output) if all_roles_ok else []
        subscription_scope = f"/subscriptions/{deployment_subscription}".lower()
        subscription_owner = any(
            item.get("roleDefinitionName") == "Owner"
            and str(item.get("scope", "")).lower() == subscription_scope
            for item in all_assignments or []
        )
    owner_status = CheckStatus.NOT_EXERCISED
    owner_message = "Deployment identity object ID is not configured."
    if object_id:
        owner_status = CheckStatus.FAILED if subscription_owner else CheckStatus.PASSED
        owner_message = (
            "Deployment identity has prohibited subscription-level Owner."
            if subscription_owner
            else "No subscription-level Owner assignment was found for the deployment identity."
        )
    checks.append(_check("subscription_owner_absent", owner_status, owner_message))
    checks.append(
        _check(
            "oidc_token_exchange",
            CheckStatus.NOT_EXERCISED,
            "Only a GitHub Actions workflow can prove OIDC token exchange.",
        )
    )

    sku = config["compute_size"]
    region = config["location"]
    sku_ok, sku_output = _run_read_only(
        [
            "az",
            "vm",
            "list-skus",
            "--location",
            region,
            "--resource-type",
            "virtualMachines",
            "--size",
            sku,
            "--subscription",
            deployment_subscription,
            "--output",
            "json",
        ]
    )
    sku_entries = _json(sku_output) if sku_ok else []
    exact_sku = next(
        (item for item in sku_entries or [] if str(item.get("name", "")).lower() == sku.lower()),
        None,
    )
    restrictions = (exact_sku or {}).get("restrictions", [])
    sku_available = bool(exact_sku and not restrictions)
    checks.append(
        _check(
            "compute_sku_availability",
            CheckStatus.PASSED if sku_available else CheckStatus.FAILED,
            (
                "Selected compute SKU is currently available."
                if sku_available
                else "Selected compute SKU is unavailable or restricted."
            ),
            region=region,
            sku=sku,
            restrictions=restrictions,
        )
    )

    capabilities = {
        item.get("name"): item.get("value") for item in (exact_sku or {}).get("capabilities", [])
    }
    family = str((exact_sku or {}).get("family", ""))
    vcpus = int(capabilities.get("vCPUs", capabilities.get("vCPUsAvailable", 0)) or 0)
    training_max = int(plan["applied_defaults"]["training_compute_max_instances"])
    batch_max = int(plan["applied_defaults"]["batch_compute_max_instances"])
    required_vcpus = vcpus * (training_max + batch_max)
    usage_ok, usage_output = _run_read_only(
        [
            "az",
            "vm",
            "list-usage",
            "--location",
            region,
            "--subscription",
            deployment_subscription,
            "--output",
            "json",
        ]
    )
    usages = _json(usage_output) if usage_ok else []
    family_usage = next(
        (
            item
            for item in usages or []
            if str(item.get("name", {}).get("value", "")).lower() == family.lower()
        ),
        None,
    )
    current = int((family_usage or {}).get("currentValue", 0))
    limit = int((family_usage or {}).get("limit", 0))
    quota_sufficient = bool(family_usage and vcpus and current + required_vcpus <= limit)
    checks.append(
        _check(
            "compute_quota_sufficiency",
            CheckStatus.PASSED if quota_sufficient else CheckStatus.FAILED,
            (
                "Current VM-family quota covers configured maximum compute."
                if quota_sufficient
                else "Current VM-family quota does not cover configured maximum compute."
            ),
            region=region,
            sku=sku,
            vm_family=family or None,
            vcpus_per_node=vcpus,
            configured_max_nodes=training_max + batch_max,
            required_vcpus=required_vcpus,
            current_usage=current,
            quota_limit=limit,
            point_in_time=True,
        )
    )
    return checks


def doctor_project(project: Path, environment: str, *, cloud_checks: bool = True) -> dict[str, Any]:
    project = project.resolve()
    receipt = verify_generation(project)
    manifest = yaml.safe_load(
        (project / "platform" / "source-manifest.yaml").read_text(encoding="utf-8")
    )
    plan = json.loads(
        (project / "platform" / "resolved-plan.json").read_text(encoding="utf-8")
    )
    checks: list[dict[str, Any]] = []
    for executable in ("git", "terraform", "az"):
        available = shutil.which(executable) is not None
        checks.append(
            _check(
                f"tool:{executable}",
                CheckStatus.PASSED if available else CheckStatus.FAILED,
                f"{executable} is available." if available else f"{executable} is unavailable.",
            )
        )
    checks.append(
        _check(
            "generation_receipt",
            CheckStatus.PASSED,
            "Generation receipt and all constituent digests are valid.",
            generation_id=receipt["generation_id"],
        )
    )
    backend_file = project / "infra" / "terraform" / f"backend-{environment}.hcl"
    checks.append(
        _check(
            "terraform_backend_config",
            CheckStatus.PASSED if backend_file.is_file() else CheckStatus.FAILED,
            (
                "Terraform backend configuration exists."
                if backend_file.is_file()
                else "Terraform backend configuration is missing."
            ),
        )
    )
    if cloud_checks and shutil.which("az"):
        checks.extend(
            _cloud_checks(
                project=project,
                manifest=manifest,
                plan=plan,
                environment=environment,
            )
        )
    else:
        checks.extend(_not_exercised_cloud_checks())
    overall = _overall_status(checks)
    return {
        "project": manifest["product"]["name"],
        "environment": environment,
        "scope": "authenticated_read_only" if cloud_checks else "offline",
        "overall_status": overall,
        "ok": overall != CheckStatus.FAILED.value,
        "checks": checks,
    }


def doctor_json(project: Path, environment: str, *, cloud_checks: bool = True) -> str:
    return json.dumps(
        doctor_project(project, environment, cloud_checks=cloud_checks), indent=2, sort_keys=True
    )
