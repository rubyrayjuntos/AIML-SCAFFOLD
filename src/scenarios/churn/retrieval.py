from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from platform_core.contracts.models import Evidence
from platform_core.settings.config import Settings


class RetrievalAdapterUnavailable(RuntimeError):
    """Raised when the local process is not configured for live retrieval."""


class RetrievalWorkspace(Protocol):
    def query_index(
        self,
        index_name: str,
        *,
        columns: list[str],
        query_text: str,
        filters: dict[str, Any] | None,
        num_results: int,
    ) -> Any: ...


def _as_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if hasattr(value, "as_dict"):
        return value.as_dict()
    return {}


def _rows(response: Any) -> list[list[Any]]:
    payload = _as_dict(response)
    result = payload.get("result", getattr(response, "result", None))
    data_array = _as_dict(result).get("data_array", getattr(result, "data_array", None))
    return data_array or []


@dataclass
class DatabricksRetrievalAdapter:
    workspace: RetrievalWorkspace
    settings: Settings

    @classmethod
    def from_settings(cls, settings: Settings) -> DatabricksRetrievalAdapter:
        if not settings.databricks_sql_warehouse_id:
            raise RetrievalAdapterUnavailable("DATABRICKS_SQL_WAREHOUSE_ID is not configured")
        if not settings.vector_search_endpoint:
            raise RetrievalAdapterUnavailable("vector_search_endpoint is not configured")

        from databricks.sdk import WorkspaceClient

        return cls(
            workspace=_DatabricksRetrievalWorkspace(
                WorkspaceClient(), catalog=settings.databricks_catalog
            ),
            settings=settings,
        )

    def retrieve_customer_evidence(
        self, customer_id: str, *, query_text: str = "", limit: int = 5
    ) -> list[Evidence]:
        evidence: list[Evidence] = []
        for index_name, source_type, columns in (
            ("notes_vs", "note", ["note_id", "note_text"]),
            ("tickets_vs", "ticket", ["ticket_id", "description"]),
        ):
            rows = _rows(
                self.workspace.query_index(
                    index_name,
                    columns=columns,
                    query_text=query_text,
                    filters={"customer_id": customer_id},
                    num_results=limit,
                )
            )
            for row in rows:
                source_id, excerpt = row[0], row[1]
                evidence.append(
                    Evidence(
                        source_id=str(source_id),
                        source_type=source_type,
                        excerpt=str(excerpt),
                    )
                )
        return evidence

    def retrieve_playbooks(self, query_text: str, *, limit: int = 3) -> list[Evidence]:
        rows = _rows(
            self.workspace.query_index(
                "playbooks_vs",
                columns=["action_id", "description"],
                query_text=query_text,
                filters=None,
                num_results=limit,
            )
        )
        return [
            Evidence(source_id=str(row[0]), source_type="playbook", excerpt=str(row[1]))
            for row in rows
        ]


class _DatabricksRetrievalWorkspace:
    def __init__(self, client: Any, *, catalog: str) -> None:
        self.client = client
        self.catalog = catalog

    def query_index(
        self,
        index_name: str,
        *,
        columns: list[str],
        query_text: str,
        filters: dict[str, Any] | None,
        num_results: int,
    ) -> Any:
        # NOTE: implementation-time verification point (see the R3 retrieval plan) -
        # confirm the installed databricks-sdk version's query_index signature matches
        # this call, in particular whether it expects `filters_json` (a JSON string)
        # rather than a raw `filters` dict.
        full_index_name = f"{self.catalog}.gold.{index_name}"
        return self.client.vector_search_indexes.query_index(
            index_name=full_index_name,
            columns=columns,
            query_text=query_text,
            filters_json=None if filters is None else _filters_to_json(filters),
            num_results=num_results,
        )


def _filters_to_json(filters: dict[str, Any]) -> str:
    import json

    return json.dumps(filters)
