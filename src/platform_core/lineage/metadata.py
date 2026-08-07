from __future__ import annotations

import hashlib
import json
from typing import Any


def evaluation_set_hash(rows: list[dict[str, Any]]) -> str:
    payload = json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def required_lineage_fields() -> tuple[str, ...]:
    return (
        "git_sha",
        "workflow_run_id",
        "source_dataset",
        "source_row_count",
        "feature_schema_version",
        "evaluation_set_hash",
        "code_version",
        "environment",
        "catalog",
        "schema_name",
    )
