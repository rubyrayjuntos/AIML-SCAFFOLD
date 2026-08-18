#!/usr/bin/env python3
"""Create and verify the infra/platform_foundation Terraform plan review artifact.

Deliberately minimal compared to the generated-project version of this script
(src/aiml_scaffold/templates/azure_ml_batch/scripts/plan_artifact.py): this
root is hand-authored in the factory itself, not generated, so there is no
generation-receipt, manifest-digest, resolved-plan-digest, or deployment-plan
governance to verify. What's kept is the part that generalizes: binding a
plan's digest to the exact run/attempt/environment that produced it, redacting
sensitive values before anything is uploaded as an artifact, and confirming
backend state hasn't drifted between plan and apply.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
from copy import deepcopy
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "1.0"
EXPECTED_FILES = {
    "plan.tfplan",
    "plan.tfplan.sha256",
    "plan.sanitized.json",
    "plan.sanitized.json.sha256",
    "approval-metadata.json",
    "artifact-manifest.json",
}
SENSITIVE_FIELD_KEYS = {
    "access_key",
    "account_key",
    "client_secret",
    "connection_string",
    "password",
    "primary_access_key",
    "primary_connection_string",
    "sas_token",
    "secret_value",
    "secondary_access_key",
    "secondary_connection_string",
}
REDACTED = "<redacted:sensitive>"
DEFAULT_RETENTION_DAYS = 30
DEFAULT_MAXIMUM_PLAN_AGE_HOURS = 24


def _sha256(path: Path) -> str:
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"


def _write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )


def _write_digest(path: Path, digest: str, target: str) -> None:
    path.write_text(f"{digest}  {target}\n", encoding="utf-8", newline="\n")


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _mask(value: Any, sensitive: Any) -> Any:
    if sensitive is True:
        return REDACTED
    if isinstance(value, dict) and isinstance(sensitive, dict):
        return {key: _mask(item, sensitive.get(key)) for key, item in value.items()}
    if isinstance(value, list) and isinstance(sensitive, list):
        return [
            _mask(item, sensitive[index] if index < len(sensitive) else None)
            for index, item in enumerate(value)
        ]
    return value


def _sanitize(node: Any, parent_key: str = "") -> Any:
    if parent_key.lower() in SENSITIVE_FIELD_KEYS:
        return REDACTED
    if isinstance(node, list):
        return [_sanitize(item, parent_key) for item in node]
    if not isinstance(node, dict):
        return node

    result = deepcopy(node)
    for value_key, sensitive_key in (
        ("values", "sensitive_values"),
        ("before", "before_sensitive"),
        ("after", "after_sensitive"),
    ):
        if value_key in result and sensitive_key in result:
            result[value_key] = _mask(result[value_key], result[sensitive_key])
    if result.get("sensitive") is True:
        for key in ("before", "after"):
            if key in result:
                result[key] = REDACTED
    return {key: _sanitize(value, key) for key, value in result.items()}


def _assert_no_credentials(node: Any) -> None:
    if isinstance(node, dict):
        for key, value in node.items():
            if key.lower() in SENSITIVE_FIELD_KEYS and value != REDACTED:
                raise ValueError("sanitized plan contains an unredacted sensitive field")
            _assert_no_credentials(value)
        return
    if isinstance(node, list):
        for value in node:
            _assert_no_credentials(value)
        return
    if not isinstance(node, str) or node == REDACTED:
        return
    lowered = node.lower()
    if "defaultendpointsprotocol=" in lowered or "accountkey=" in lowered:
        raise ValueError("sanitized plan contains a credential-bearing value")


def _action_summary(plan: dict[str, Any]) -> dict[str, int]:
    summary = {"create": 0, "update": 0, "replace": 0, "delete": 0, "read": 0, "no_op": 0}
    for change in plan.get("resource_changes", []):
        actions = change.get("change", {}).get("actions", [])
        if actions == ["create"]:
            summary["create"] += 1
        elif actions == ["update"]:
            summary["update"] += 1
        elif "create" in actions and "delete" in actions:
            summary["replace"] += 1
        elif actions == ["delete"]:
            summary["delete"] += 1
        elif actions == ["read"]:
            summary["read"] += 1
        elif actions == ["no-op"]:
            summary["no_op"] += 1
        else:
            raise ValueError("Terraform plan contains an unsupported action sequence")
    return summary


def _state_identity(path: Path) -> dict[str, Any]:
    if not path.exists() or not path.read_bytes().strip():
        return {"exists": False, "lineage": None, "serial": None}
    payload = _read_json(path)
    lineage = payload.get("lineage") if isinstance(payload, dict) else None
    serial = payload.get("serial") if isinstance(payload, dict) else None
    return {"exists": True, "lineage": lineage, "serial": serial}


def create(args: argparse.Namespace) -> None:
    root = Path(args.artifact_dir).resolve()
    root.mkdir(parents=True, exist_ok=True)
    plan_path = Path(args.plan).resolve()
    raw_path = Path(args.raw_json).resolve()
    if plan_path.parent != root:
        raise ValueError("binary plan must be in the artifact directory")
    raw = _read_json(raw_path)
    sanitized = _sanitize(raw)
    _assert_no_credentials(sanitized)

    sanitized_path = root / "plan.sanitized.json"
    _write_json(sanitized_path, sanitized)
    plan_digest = _sha256(plan_path)
    json_digest = _sha256(sanitized_path)
    _write_digest(root / "plan.tfplan.sha256", plan_digest, "plan.tfplan")
    _write_digest(root / "plan.sanitized.json.sha256", json_digest, "plan.sanitized.json")

    created_at = datetime.now(UTC)
    approval = {
        "approval_contract_version": SCHEMA_VERSION,
        "source_commit": args.source_commit,
        "target_environment": args.environment,
        "plan_digest": plan_digest,
        "json_digest": json_digest,
        "plan_run_id": args.run_id,
        "plan_run_attempt": args.run_attempt,
        "plan_requested_by": args.actor,
    }
    _write_json(root / "approval-metadata.json", approval)

    state_snapshot = Path(args.state_snapshot).resolve()
    manifest = {
        "artifact_manifest_schema_version": SCHEMA_VERSION,
        "created_at": created_at.isoformat(),
        "expires_at": (created_at + timedelta(days=args.retention_days)).isoformat(),
        "maximum_plan_age_hours": args.maximum_plan_age_hours,
        "source_commit": args.source_commit,
        "target_environment": args.environment,
        "plan_run_id": args.run_id,
        "plan_run_attempt": args.run_attempt,
        "plan_digest": plan_digest,
        "json_digest": json_digest,
        "state": _state_identity(state_snapshot),
        "action_summary": _action_summary(sanitized),
    }
    _write_json(root / "artifact-manifest.json", manifest)
    raw_path.unlink(missing_ok=True)
    verify_artifact(root)


def _read_digest(path: Path, expected_name: str) -> str:
    match = re.fullmatch(r"(sha256:[0-9a-f]{64})  ([^\n]+)\n?", path.read_text(encoding="utf-8"))
    if not match or match.group(2) != expected_name:
        raise ValueError("artifact digest file is malformed")
    return match.group(1)


def verify_artifact(
    root: Path,
    *,
    expected_run_id: str | None = None,
    expected_run_attempt: str | None = None,
    expected_environment: str | None = None,
    reviewed_plan_digest: str | None = None,
    reviewed_json_digest: str | None = None,
    current_state_snapshot: Path | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    actual_files = {path.name for path in root.iterdir() if path.is_file()}
    if actual_files != EXPECTED_FILES:
        raise ValueError("reviewed artifact contents do not match schema 1.0")
    manifest = _read_json(root / "artifact-manifest.json")
    if manifest.get("artifact_manifest_schema_version") != SCHEMA_VERSION:
        raise ValueError("unsupported artifact manifest schema")

    plan_digest = _sha256(root / "plan.tfplan")
    json_path = root / "plan.sanitized.json"
    json_digest = _sha256(json_path)
    sanitized = _read_json(json_path)
    _assert_no_credentials(sanitized)
    approval = _read_json(root / "approval-metadata.json")
    checked_at = (now or datetime.now(UTC)).astimezone(UTC)
    created_at = datetime.fromisoformat(manifest["created_at"])
    expires_at = datetime.fromisoformat(manifest["expires_at"])
    maximum_age = manifest.get("maximum_plan_age_hours")

    checks = {
        "created_not_future": created_at <= checked_at,
        "not_expired": checked_at <= expires_at,
        "within_maximum_age": checked_at - created_at <= timedelta(hours=maximum_age),
        "plan_digest_file": _read_digest(root / "plan.tfplan.sha256", "plan.tfplan") == plan_digest,
        "json_digest_file": _read_digest(root / "plan.sanitized.json.sha256", "plan.sanitized.json")
        == json_digest,
        "manifest_plan_digest": manifest.get("plan_digest") == plan_digest,
        "manifest_json_digest": manifest.get("json_digest") == json_digest,
        "manifest_action_summary": manifest.get("action_summary") == _action_summary(sanitized),
        "approval_version": approval.get("approval_contract_version") == SCHEMA_VERSION,
        "approval_plan_digest": approval.get("plan_digest") == plan_digest,
        "approval_json_digest": approval.get("json_digest") == json_digest,
        "approval_commit": approval.get("source_commit") == manifest.get("source_commit"),
        "approval_environment": approval.get("target_environment")
        == manifest.get("target_environment"),
        "approval_run": approval.get("plan_run_id") == manifest.get("plan_run_id"),
        "approval_attempt": approval.get("plan_run_attempt") == manifest.get("plan_run_attempt"),
        "source_commit": bool(re.fullmatch(r"[0-9a-f]{40}", manifest.get("source_commit", ""))),
    }
    if expected_run_id is not None:
        checks["expected_run"] = manifest.get("plan_run_id") == expected_run_id
    if expected_run_attempt is not None:
        checks["expected_attempt"] = manifest.get("plan_run_attempt") == expected_run_attempt
    if expected_environment is not None:
        checks["expected_environment"] = manifest.get("target_environment") == expected_environment
    if reviewed_plan_digest is not None:
        checks["reviewed_plan_digest"] = reviewed_plan_digest.lower() == plan_digest
    if reviewed_json_digest is not None:
        checks["reviewed_json_digest"] = reviewed_json_digest.lower() == json_digest
    if current_state_snapshot is not None:
        checks["backend_state_unchanged"] = manifest.get("state") == _state_identity(
            current_state_snapshot
        )
    failed = sorted(name for name, passed in checks.items() if not passed)
    if failed:
        raise ValueError("artifact verification failed: " + ", ".join(failed))
    return manifest


def verify(args: argparse.Namespace) -> None:
    manifest = verify_artifact(
        Path(args.artifact_dir).resolve(),
        expected_run_id=args.run_id,
        expected_run_attempt=args.run_attempt,
        expected_environment=args.environment,
        reviewed_plan_digest=args.plan_digest,
        reviewed_json_digest=args.json_digest,
        current_state_snapshot=(
            Path(args.current_state_snapshot).resolve() if args.current_state_snapshot else None
        ),
    )
    if args.github_output:
        output = Path(os.environ["GITHUB_OUTPUT"])
        approval = _read_json(Path(args.artifact_dir).resolve() / "approval-metadata.json")
        with output.open("a", encoding="utf-8") as stream:
            stream.write(f"source_commit={manifest['source_commit']}\n")
            stream.write(f"plan_requested_by={approval['plan_requested_by']}\n")
            stream.write(f"plan_digest={manifest['plan_digest']}\n")
            stream.write(f"json_digest={manifest['json_digest']}\n")


def _terraform_version(terraform_dir: Path) -> None:
    subprocess.run(
        ["terraform", f"-chdir={terraform_dir}", "version", "-json"],
        check=True,
        capture_output=True,
        text=True,
    )


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser()
    commands = result.add_subparsers(dest="command", required=True)

    create_parser = commands.add_parser("create")
    for name in (
        "artifact-dir",
        "terraform-dir",
        "plan",
        "raw-json",
        "source-commit",
        "run-id",
        "run-attempt",
        "actor",
        "environment",
        "state-snapshot",
    ):
        create_parser.add_argument(f"--{name}", required=True)
    create_parser.add_argument("--retention-days", type=int, default=DEFAULT_RETENTION_DAYS)
    create_parser.add_argument(
        "--maximum-plan-age-hours", type=int, default=DEFAULT_MAXIMUM_PLAN_AGE_HOURS
    )
    create_parser.set_defaults(handler=create)

    verify_parser = commands.add_parser("verify")
    verify_parser.add_argument("--artifact-dir", required=True)
    verify_parser.add_argument("--run-id")
    verify_parser.add_argument("--run-attempt")
    verify_parser.add_argument("--environment")
    verify_parser.add_argument("--plan-digest")
    verify_parser.add_argument("--json-digest")
    verify_parser.add_argument("--current-state-snapshot")
    verify_parser.add_argument("--github-output", action="store_true")
    verify_parser.set_defaults(handler=verify)
    return result


def main() -> int:
    args = parser().parse_args()
    if args.command == "create":
        _terraform_version(Path(args.terraform_dir))
    try:
        args.handler(args)
    except (
        KeyError,
        OSError,
        ValueError,
        json.JSONDecodeError,
        subprocess.CalledProcessError,
    ) as error:
        raise SystemExit(f"plan artifact validation failed: {error}") from None
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
