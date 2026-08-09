from __future__ import annotations

from datetime import date, timedelta
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse

from platform_core.contracts.models import (
    AssistantRequest,
    AssistantResponse,
    Evidence,
    ResponseEnvelope,
    ScoreResponse,
    SnapshotDelta,
)
from platform_core.integrations.databricks_serving import (
    DatabricksServingAdapter,
    ServingAdapterUnavailable,
)
from platform_core.settings.config import settings

app = FastAPI(title="Enterprise ML Workflow API", version="1.0.0")
API_CONTRACT_VERSION = "2026-08-07"


def request_id() -> str:
    return str(uuid4())


def _reference_score(entity_id: str, rid: str) -> ScoreResponse:
    # Reference adapter boundary. Production replaces this with the Databricks
    # client; the API contract and provenance fields remain unchanged.
    return ScoreResponse(
        entity_id=entity_id,
        score=0.5,
        drivers={"reference_signal": 0.0},
        model_version="unavailable",
        served_version="unavailable",
        feature_version="unavailable",
        feature_contract="unavailable",
        request_id=rid,
    )


def _score(entity_id: str, rid: str) -> ScoreResponse:
    try:
        return DatabricksServingAdapter.from_settings(settings).score(entity_id, rid)
    except (ServingAdapterUnavailable, ImportError):
        return _reference_score(entity_id, rid)


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    rid = request.headers.get("x-request-id", request_id())
    request.state.request_id = rid
    response = await call_next(request)
    response.headers["x-request-id"] = rid
    return response


@app.exception_handler(HTTPException)
async def http_error(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "request_id": request.state.request_id,
            "source": str(request.url.path),
            "version": API_CONTRACT_VERSION,
            "status": "error",
            "data": {"error": "request_error", "message": str(exc.detail)},
        },
    )


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1/score", response_model=ResponseEnvelope[ScoreResponse])
def score(
    customer_id: str = Query(min_length=1), request: Request = None
) -> ResponseEnvelope[ScoreResponse]:
    result = _score(customer_id, request.state.request_id)
    return ResponseEnvelope(
        request_id=result.request_id,
        source="/api/v1/score",
        version=API_CONTRACT_VERSION,
        status="success",
        data=result,
    )


@app.get("/api/v1/diff", response_model=ResponseEnvelope[SnapshotDelta])
def diff(
    customer_id: str = Query(min_length=1),
    window: str = Query(default="30d", pattern=r"^(7d|30d|90d)$"),
    request: Request = None,
) -> ResponseEnvelope[SnapshotDelta]:
    rid = request.state.request_id
    days = int(window[:-1])
    result = SnapshotDelta(
        current_snapshot=date.today(),
        previous_snapshot=date.today() - timedelta(days=days),
        deltas={"reference_signal": 0.0},
        request_id=rid,
    )
    return ResponseEnvelope(
        request_id=rid,
        source="/api/v1/diff",
        version=API_CONTRACT_VERSION,
        status="success",
        data=result,
    )


@app.post("/api/v1/assistant", response_model=ResponseEnvelope[AssistantResponse])
def assistant(
    payload: AssistantRequest, request: Request = None
) -> ResponseEnvelope[AssistantResponse]:
    rid = request.state.request_id
    _score(payload.entity_id, rid)  # authoritative context is derived server-side
    result = AssistantResponse(
        entity_id=payload.entity_id,
        risk_explanation=(
            "No live model or Foundry deployment is configured in this reference process."
        ),
        what_changed="No live snapshot comparison is available.",
        recommended_action="Configure the deployed scenario adapter before production use.",
        evidence=[
            Evidence(
                source_id="reference",
                source_type="metric",
                excerpt="Reference adapter response",
            )
        ],
        model_version="unavailable",
        response_source="deterministic_fallback",
        request_id=rid,
    )
    return ResponseEnvelope(
        request_id=rid,
        source="/api/v1/assistant",
        version=API_CONTRACT_VERSION,
        status="success",
        data=result,
    )
