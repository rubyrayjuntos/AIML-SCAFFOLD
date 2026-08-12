from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined, TemplateNotFound

from platform_core.contracts.product_manifest import ProductManifest
from platform_core.contracts.project_plan import ResolvedProjectPlan
from platform_core.contracts.resolver import resolve_project_plan

RECEIPT_NAME = "generation-receipt.json"
IGNORED_RUNTIME_PARTS = {
    ".git",
    ".terraform",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
}


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _digest_bytes(value: bytes) -> str:
    return f"sha256:{hashlib.sha256(value).hexdigest()}"


def _digest_json(value: Any) -> str:
    return _digest_bytes(_canonical_json(value).encode("utf-8"))


def _arm_leaf(resource_id: str) -> str:
    return resource_id.rstrip("/").split("/")[-1]


def template_root() -> Path:
    return Path(__file__).resolve().parent / "templates" / "azure_ml_batch"


def template_digest(root: Path | None = None) -> str:
    source = root or template_root()
    digest = hashlib.sha256()
    for path in sorted(file for file in source.rglob("*") if file.is_file()):
        relative = path.relative_to(source).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return f"sha256:{digest.hexdigest()}"


def generated_files_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(file for file in root.rglob("*") if file.is_file()):
        relative = path.relative_to(root).as_posix()
        if relative == RECEIPT_NAME:
            continue
        if any(part in IGNORED_RUNTIME_PARTS for part in path.relative_to(root).parts):
            continue
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return f"sha256:{digest.hexdigest()}"


def verify_generation(root: Path) -> dict[str, Any]:
    receipt_path = root / RECEIPT_NAME
    if not receipt_path.is_file():
        raise ValueError(f"missing {RECEIPT_NAME}")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    actual = generated_files_digest(root)
    if receipt.get("generated_files_digest") != actual:
        raise ValueError(
            f"generated tree digest mismatch: receipt={receipt.get('generated_files_digest')} "
            f"actual={actual}"
        )
    source_manifest = yaml.safe_load(
        (root / "platform" / "source-manifest.yaml").read_text(encoding="utf-8")
    )
    resolved_plan = json.loads(
        (root / "platform" / "resolved-plan.json").read_text(encoding="utf-8")
    )
    expected = {
        "manifest_digest": _digest_json(source_manifest),
        "resolved_plan_digest": _digest_json(resolved_plan),
        "template_digest": template_digest(),
        "dependency_constraints_digest": _digest_bytes(
            (root / "constraints.txt").read_bytes()
        ),
    }
    for field, digest in expected.items():
        if receipt.get(field) != digest:
            raise ValueError(
                f"generation receipt {field} mismatch: receipt={receipt.get(field)} "
                f"actual={digest}"
            )
    expected_generation_id = _digest_json(
        {
            "platform_version": receipt["platform_version"],
            "manifest_digest": expected["manifest_digest"],
            "resolved_plan_digest": expected["resolved_plan_digest"],
            "template_digest": expected["template_digest"],
            "generated_files_digest": actual,
        }
    )
    if receipt.get("generation_id") != expected_generation_id:
        raise ValueError("generation receipt generation_id mismatch")
    return receipt


def generate_project(
    manifest: ProductManifest,
    output: Path,
    *,
    environment: str = "dev",
    allow_experimental: bool = False,
) -> tuple[ResolvedProjectPlan, dict[str, Any]]:
    if not template_root().is_dir():
        raise TemplateNotFound(str(template_root()))
    if output.exists() and not output.is_dir():
        raise NotADirectoryError(f"output path is not a directory: {output}")
    if output.exists() and any(output.iterdir()):
        raise ValueError(f"output directory must be empty: {output}")
    output.mkdir(parents=True, exist_ok=True)
    plan = resolve_project_plan(
        manifest, environment, allow_experimental=allow_experimental
    )
    backend = manifest.shared_resources.terraform_backend
    context = {
        "manifest": manifest.canonical_dict(),
        "plan": plan.canonical_dict(),
        "project_name": manifest.product.name,
        "project_python_name": manifest.product.name.replace("-", "_"),
        "environment": environment,
        "location": plan.applied_defaults["location"],
        "compute_size": plan.applied_defaults["compute_size"],
        "batch_compute_max_instances": plan.applied_defaults["batch_compute_max_instances"],
        "training_compute_max_instances": plan.applied_defaults[
            "training_compute_max_instances"
        ],
        "evidence_retention_days": plan.applied_defaults["evidence_retention_days"],
        "terraform_state_key": plan.applied_defaults["terraform_state_key"],
        "backend_resource_group": _arm_leaf(backend.resource_group_id),
        "backend_storage_account": _arm_leaf(backend.storage_account_id),
        "backend_container": backend.container_name,
        "model_name": f"{manifest.product.name}-model",
        "batch_endpoint_name": f"{manifest.product.name}-batch",
    }
    environment_renderer = Environment(
        loader=FileSystemLoader(str(template_root())),
        undefined=StrictUndefined,
        variable_start_string="[[",
        variable_end_string="]]",
        autoescape=False,
        keep_trailing_newline=True,
        newline_sequence="\n",
    )
    for source in sorted(path for path in template_root().rglob("*") if path.is_file()):
        relative = source.relative_to(template_root()).as_posix()
        destination_relative = relative[:-3] if relative.endswith(".j2") else relative
        destination = output / destination_relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        if relative.endswith(".j2"):
            rendered = environment_renderer.get_template(relative).render(**context)
            destination.write_text(rendered, encoding="utf-8", newline="\n")
        else:
            destination.write_bytes(source.read_bytes())

    platform_directory = output / "platform"
    platform_directory.mkdir(parents=True, exist_ok=True)
    source_manifest = manifest.source_dict()
    (platform_directory / "source-manifest.yaml").write_text(
        yaml.safe_dump(source_manifest, allow_unicode=True, sort_keys=True),
        encoding="utf-8",
        newline="\n",
    )
    (platform_directory / "resolved-plan.json").write_text(
        json.dumps(plan.canonical_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    files_digest = generated_files_digest(output)
    manifest_digest = _digest_json(source_manifest)
    plan_digest = _digest_json(plan.canonical_dict())
    source_template_digest = template_digest()
    generation_id = _digest_json(
        {
            "platform_version": manifest.platform_version,
            "manifest_digest": manifest_digest,
            "resolved_plan_digest": plan_digest,
            "template_digest": source_template_digest,
            "generated_files_digest": files_digest,
        }
    )
    receipt = {
        "receipt_schema_version": "1.0",
        "platform_version": manifest.platform_version,
        "manifest_digest": manifest_digest,
        "resolved_plan_digest": plan_digest,
        "template_digest": source_template_digest,
        "generated_files_digest": files_digest,
        "dependency_constraints_digest": _digest_bytes(
            (output / "constraints.txt").read_bytes()
        ),
        "generation_id": generation_id,
        "capabilities": ["ml"],
        "providers": plan.providers,
    }
    (output / RECEIPT_NAME).write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return plan, receipt
