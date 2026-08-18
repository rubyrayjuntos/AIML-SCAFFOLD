from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml
from jinja2 import TemplateNotFound
from pydantic import ValidationError

from aiml_scaffold.doctor import doctor_project
from aiml_scaffold.generator import generate_project
from platform_core.contracts.product_manifest import ProductManifest
from platform_core.contracts.resolver import resolve_project_plan
from platform_core.policy.evaluator import evaluate_policy


def _add_experimental_flag(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--allow-experimental",
        action="store_true",
        help="Allow implemented non-stable providers when the manifest policy also permits them.",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="aiml-scaffold")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate")
    validate.add_argument("manifest", type=Path)
    _add_experimental_flag(validate)

    plan = subparsers.add_parser("plan")
    plan.add_argument("manifest", type=Path)
    plan.add_argument("--environment", default="dev")
    plan.add_argument("--output", type=Path)
    _add_experimental_flag(plan)

    generate = subparsers.add_parser("generate")
    generate.add_argument("manifest", type=Path)
    generate.add_argument("--environment", default="dev")
    generate.add_argument("--output", type=Path, required=True)
    generate.add_argument("--platform-source-commit")
    generate.add_argument("--platform-package-digest")
    _add_experimental_flag(generate)

    doctor = subparsers.add_parser("doctor")
    doctor.add_argument("project", type=Path)
    doctor.add_argument("--environment", default="dev")
    doctor.add_argument("--no-cloud", action="store_true")
    return parser


def _safe_path(path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        resolved = path.resolve()
        working_directory = Path.cwd().resolve()
        if resolved.is_relative_to(working_directory):
            return str(resolved.relative_to(working_directory))
    except OSError:
        pass
    return f"<absolute>/{path.name}" if path.is_absolute() else str(path)


def _failure(command: str, code: str, message: str, *, path: Path | None = None) -> dict:
    error = {"code": code, "message": message}
    safe_path = _safe_path(path)
    if safe_path:
        error["path"] = safe_path
    return {"ok": False, "command": command, "error": error}


def _maturity_report(manifest: ProductManifest, allow_experimental: bool) -> dict:
    return {
        "release_status": "preview",
        "manifest_policy": manifest.policy.capability_maturity.value,
        "cli_override_supplied": allow_experimental,
        "authorization_result": "allowed",
        "remaining_evidence_boundary": "dev_live_pending",
    }


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "doctor":
            payload = doctor_project(
                args.project, args.environment, cloud_checks=not args.no_cloud
            )
            print(json.dumps(payload, indent=2, sort_keys=True))
            return 0 if payload["ok"] else 1

        manifest = ProductManifest.load(args.manifest)
        if args.command == "validate":
            descriptors = evaluate_policy(
                manifest, allow_experimental=args.allow_experimental
            )
            print(
                json.dumps(
                    {
                        "ok": True,
                        "valid": True,
                        "project": manifest.product.name,
                        "maturity": _maturity_report(
                            manifest, args.allow_experimental
                        ),
                        "capabilities": [
                            descriptor.model_dump(mode="json") for descriptor in descriptors
                        ],
                    },
                    indent=2,
                    sort_keys=True,
                )
            )
            return 0
        if args.command == "plan":
            plan = resolve_project_plan(
                manifest,
                args.environment,
                allow_experimental=args.allow_experimental,
            )
            rendered = json.dumps(plan.canonical_dict(), indent=2, sort_keys=True) + "\n"
            if args.output:
                args.output.write_text(rendered, encoding="utf-8", newline="\n")
            else:
                print(rendered, end="")
            return 0
        if args.command == "generate":
            plan, receipt = generate_project(
                manifest,
                args.output,
                environment=args.environment,
                allow_experimental=args.allow_experimental,
                platform_source_commit=args.platform_source_commit,
                platform_package_digest=args.platform_package_digest,
            )
            print(
                json.dumps(
                    {
                        "generated": str(args.output),
                        "generation_id": receipt["generation_id"],
                        "resources": [
                            resource.model_dump(mode="json") for resource in plan.resources
                        ],
                    },
                    indent=2,
                    sort_keys=True,
                )
            )
            return 0
    except (json.JSONDecodeError, yaml.YAMLError):
        path = getattr(args, "project", None) or getattr(args, "manifest", None)
        print(
            json.dumps(
                _failure(
                    args.command,
                    "DOCUMENT_FORMAT_INVALID",
                    "A required JSON or YAML document is malformed.",
                    path=path,
                ),
                indent=2,
                sort_keys=True,
            )
        )
        return 4
    except (ValidationError, ValueError) as exc:
        code = "GENERATED_INTEGRITY_FAILED" if args.command == "doctor" else "VALIDATION_FAILED"
        path = (
            getattr(args, "project", None)
            if args.command == "doctor"
            else getattr(args, "manifest", None)
        )
        print(
            json.dumps(
                _failure(
                    args.command,
                    code,
                    str(exc),
                    path=path,
                ),
                indent=2,
                sort_keys=True,
            )
        )
        return 2
    except FileNotFoundError:
        path = getattr(args, "manifest", None)
        code = "MANIFEST_NOT_FOUND"
        message = "The manifest file does not exist."
        if args.command == "doctor":
            path = args.project
            code = "GENERATED_PROJECT_NOT_FOUND"
            message = "The generated project or required provenance file does not exist."
        print(
            json.dumps(
                _failure(args.command, code, message, path=path),
                indent=2,
                sort_keys=True,
            )
        )
        return 3
    except PermissionError:
        output_path = getattr(args, "output", None)
        code = "OUTPUT_PERMISSION_DENIED" if output_path else "INPUT_PERMISSION_DENIED"
        message = (
            "Cannot write the output directory."
            if output_path
            else "Cannot read the requested input."
        )
        print(
            json.dumps(
                _failure(args.command, code, message, path=output_path),
                indent=2,
                sort_keys=True,
            )
        )
        return 3
    except (IsADirectoryError, NotADirectoryError):
        path = getattr(args, "output", None) or getattr(args, "manifest", None)
        print(
            json.dumps(
                _failure(
                    args.command,
                    "PATH_TYPE_INVALID",
                    "The requested path has the wrong filesystem type.",
                    path=path,
                ),
                indent=2,
                sort_keys=True,
            )
        )
        return 3
    except TemplateNotFound:
        print(
            json.dumps(
                _failure(
                    args.command,
                    "TEMPLATE_CONTENT_MISSING",
                    "Installed AIML-SCAFFOLD template content is incomplete.",
                ),
                indent=2,
                sort_keys=True,
            )
        )
        return 4
    except OSError:
        path = getattr(args, "output", None) or getattr(args, "manifest", None)
        print(
            json.dumps(
                _failure(
                    args.command,
                    "FILESYSTEM_OPERATION_FAILED",
                    "The filesystem operation could not be completed.",
                    path=path,
                ),
                indent=2,
                sort_keys=True,
            )
        )
        return 3
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
