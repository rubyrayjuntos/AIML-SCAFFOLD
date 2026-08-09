#!/usr/bin/env python3
"""Explicitly promote a validated dev model version and update serving."""

from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from pathlib import Path

MODEL_NAME = "mlworkflow_dev.ml.churn_classifier"
ENDPOINT_NAME = "churn-model-endpoint"
MINIMUM_IMPROVEMENT = 0.02


def databricks(*args: str) -> dict:
    result = subprocess.run(
        ["databricks", *args, "-o", "json"],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout) if result.stdout.strip() else {}


def post_json(path: str, payload: dict) -> dict:
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as handle:
        json.dump(payload, handle)
        payload_path = Path(handle.name)
    try:
        return databricks("api", "post", path, "--json", f"@{payload_path}")
    finally:
        payload_path.unlink(missing_ok=True)


def set_alias(alias: str, version: str) -> None:
    post_json(
        "/api/2.0/mlflow/unity-catalog/registered-models/alias",
        {"name": MODEL_NAME, "alias": alias, "version": version},
    )


def endpoint_config(version: str) -> dict:
    served_model_name = f"churn-classifier-{version}"
    return {
        "served_entities": [
            {
                "name": served_model_name,
                "entity_name": MODEL_NAME,
                "entity_version": version,
                "workload_size": "Small",
                "scale_to_zero_enabled": True,
            }
        ],
        "traffic_config": {
            "routes": [{"served_model_name": served_model_name, "traffic_percentage": 100}]
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-version", required=True)
    parser.add_argument("--candidate-auc", required=True, type=float)
    parser.add_argument("--champion-auc", type=float)
    parser.add_argument("--approve", action="store_true")
    args = parser.parse_args()

    if not args.approve:
        raise SystemExit("promotion requires --approve")
    if args.champion_auc is not None:
        improvement = args.candidate_auc - args.champion_auc
        if improvement + 1e-12 < MINIMUM_IMPROVEMENT:
            raise SystemExit(
                f"AUC improvement {improvement:.4f} is below {MINIMUM_IMPROVEMENT:.4f}"
            )

    version = str(args.model_version)
    set_alias("challenger", version)
    set_alias("champion", version)
    set_alias("served", version)
    config = endpoint_config(version)
    try:
        databricks("serving-endpoints", "get", ENDPOINT_NAME)
    except subprocess.CalledProcessError:
        post_json(
            "/api/2.0/serving-endpoints",
            {"name": ENDPOINT_NAME, "config": config},
        )
    else:
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as handle:
            json.dump(config, handle)
            config_path = Path(handle.name)
        try:
            databricks(
                "serving-endpoints",
                "update-config",
                ENDPOINT_NAME,
                "--json",
                f"@{config_path}",
            )
        finally:
            config_path.unlink(missing_ok=True)

    print(
        json.dumps(
            {
                "model_name": MODEL_NAME,
                "model_version": version,
                "aliases": ["challenger", "champion", "served"],
                "endpoint": ENDPOINT_NAME,
                "candidate_auc": args.candidate_auc,
            }
        )
    )


if __name__ == "__main__":
    main()
