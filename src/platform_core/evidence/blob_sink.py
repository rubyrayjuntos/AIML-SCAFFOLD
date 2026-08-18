from __future__ import annotations

import json
from typing import Any

from platform_core.contracts.evidence import EvidenceEvent, OperationReceipt


class EvidenceConflictError(RuntimeError):
    pass


class BlobEvidenceSink:
    """Create-only Blob sink with an injected container client.

    The Azure SDK client is intentionally injected so the contract kernel remains
    importable and testable without cloud dependencies.
    """

    def __init__(self, container_client: Any) -> None:
        self.container_client = container_client

    def append(self, event: EvidenceEvent) -> str:
        return self._create_or_verify(event.blob_name, event.canonical_json())

    def write_receipt(self, receipt: OperationReceipt) -> str:
        name = f"receipts/{receipt.operation_id}/receipt.json"
        payload = json.dumps(
            receipt.model_dump(mode="json"), sort_keys=True, separators=(",", ":")
        )
        return self._create_or_verify(name, payload)

    def _create_or_verify(self, name: str, payload: str) -> str:
        client = self.container_client.get_blob_client(name)
        try:
            client.upload_blob(payload.encode("utf-8"), overwrite=False)
            return "created"
        except Exception as exc:
            try:
                existing = client.download_blob().readall().decode("utf-8")
            except Exception:
                raise exc
            if existing == payload:
                return "existing"
            raise EvidenceConflictError(
                f"evidence object {name!r} already exists with different content"
            ) from exc
