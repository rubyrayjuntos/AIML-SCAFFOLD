# Databricks notebook source
# ruff: noqa: F821
"""Idempotently create the vector search endpoint and delta-sync indexes retrieval
queries against.

The ambient databricks-sdk in this notebook's default environment predates
`embedding_model_endpoint_name` on `EmbeddingSourceColumn` - the churn_runtime
environment in workflows.yml pins databricks-sdk>=0.38 so this signature resolves.
"""
import time

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.vectorsearch import (
    DeltaSyncVectorIndexSpecRequest,
    EmbeddingSourceColumn,
    EndpointType,
    PipelineType,
    VectorIndexType,
)

dbutils.widgets.text("catalog", "mlworkflow_dev")
catalog = dbutils.widgets.get("catalog")

ENDPOINT_NAME = "churn-retrieval-endpoint"
EMBEDDING_MODEL_ENDPOINT = "databricks-gte-large-en"
POLL_TIMEOUT_SECONDS = 900
POLL_INTERVAL_SECONDS = 15

INDEXES = [
    {
        "logical_name": "notes_vs",
        "source_table": f"{catalog}.gold.customer_notes",
        "primary_key": "note_id",
        "embedding_source_column": "note_text",
    },
    {
        "logical_name": "tickets_vs",
        "source_table": f"{catalog}.gold.support_tickets",
        "primary_key": "ticket_id",
        "embedding_source_column": "description",
    },
    {
        "logical_name": "playbooks_vs",
        "source_table": f"{catalog}.gold.recommended_actions",
        "primary_key": "action_id",
        "embedding_source_column": "description",
    },
]

client = WorkspaceClient()

try:
    client.vector_search_endpoints.get_endpoint(endpoint_name=ENDPOINT_NAME)
    print(f"endpoint {ENDPOINT_NAME} already exists")
except Exception:
    client.vector_search_endpoints.create_endpoint(
        name=ENDPOINT_NAME, endpoint_type=EndpointType.STANDARD
    )
    print(f"creating endpoint {ENDPOINT_NAME}")

deadline = time.time() + POLL_TIMEOUT_SECONDS
while True:
    endpoint = client.vector_search_endpoints.get_endpoint(endpoint_name=ENDPOINT_NAME)
    state = str(getattr(endpoint, "endpoint_status", None) or getattr(endpoint, "creator", ""))
    if "ONLINE" in state.upper() or state == "":
        # Some SDK versions expose readiness differently; fall back to attempting index
        # creation below, which will itself fail loudly if the endpoint truly isn't ready.
        break
    if time.time() > deadline:
        raise TimeoutError(f"endpoint {ENDPOINT_NAME} did not become ready in time: {state}")
    time.sleep(POLL_INTERVAL_SECONDS)

def _get_status(index_name):
    return getattr(client.vector_search_indexes.get_index(index_name=index_name), "status", None)


def _poll_until_ready(index_name, timeout_message):
    """Poll get_index() until status.ready is true.

    This installed databricks-sdk version's VectorIndexStatus only exposes
    `ready`/`message`/`index_url`/`indexed_row_count` - there is no `detailed_state`
    field (the ONLINE_NO_PENDING_UPDATE state name from the vector search docs isn't
    present on this typed model), so `ready` is the only readiness signal available.
    """
    deadline = time.time() + POLL_TIMEOUT_SECONDS
    while True:
        status = _get_status(index_name)
        if bool(getattr(status, "ready", False)):
            return status
        if time.time() > deadline:
            message = getattr(status, "message", "")
            raise TimeoutError(f"{timeout_message}: last message {message!r}")
        time.sleep(POLL_INTERVAL_SECONDS)


for spec in INDEXES:
    index_name = f"{catalog}.gold.{spec['logical_name']}"
    try:
        client.vector_search_indexes.get_index(index_name=index_name)
        print(f"index {index_name} already exists")
    except Exception:
        client.vector_search_indexes.create_index(
            name=index_name,
            endpoint_name=ENDPOINT_NAME,
            primary_key=spec["primary_key"],
            index_type=VectorIndexType.DELTA_SYNC,
            delta_sync_index_spec=DeltaSyncVectorIndexSpecRequest(
                source_table=spec["source_table"],
                pipeline_type=PipelineType.TRIGGERED,
                embedding_source_columns=[
                    EmbeddingSourceColumn(
                        name=spec["embedding_source_column"],
                        embedding_model_endpoint_name=EMBEDDING_MODEL_ENDPOINT,
                    )
                ],
            ),
        )
        print(f"creating index {index_name}")

    # A freshly created index provisions asynchronously - sync_index() raises
    # BadRequest("... is not ready") if called before that finishes, so retry on
    # that specific error with backoff rather than trusting a single readiness check.
    deadline = time.time() + POLL_TIMEOUT_SECONDS
    while True:
        try:
            client.vector_search_indexes.sync_index(index_name=index_name)
            break
        except Exception as exc:
            if "not ready" not in str(exc).lower():
                raise
            if time.time() > deadline:
                raise TimeoutError(f"index {index_name} never became ready to sync") from exc
            time.sleep(POLL_INTERVAL_SECONDS)

    _poll_until_ready(index_name, f"index {index_name} did not finish syncing in time")
    print(f"index {index_name} is ready")

print(f"all {len(INDEXES)} indexes ready on endpoint {ENDPOINT_NAME}")
