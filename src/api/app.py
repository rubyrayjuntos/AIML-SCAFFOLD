from __future__ import annotations

from datetime import date, timedelta
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse

from platform_core.contracts.models import (
    AssistantRequest,
    AssistantResponse,
    Evidence,
    ScoreResponse,
    SnapshotDelta,
)

app = FastAPI(title="Enterprise ML Workflow API", version="1.0.0")


def request_id() -> str:
    return str(uuid4())


def _score(entity_id: str, rid: str) -> ScoreResponse:
    # Reference adapter boundary. Production replaces this with the Databricks
    # client; the API contract and provenance fields remain unchanged.
    return ScoreResponse(
        entity_id=entity_id,
        score=0.5,
        drivers={"reference_signal": 0.0},
        model_version="unavailable",
        served_version="unavailable",
        request_id=rid,
    )


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
            "error": "request_error",
            "message": str(exc.detail),
            "request_id": request.state.request_id,
            "details": {},
        },
    )


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1/score", response_model=ScoreResponse)
def score(customer_id: str = Query(min_length=1), request: Request = None) -> ScoreResponse:
    return _score(customer_id, request.state.request_id)


@app.get("/api/v1/diff", response_model=SnapshotDelta)
def diff(
    customer_id: str = Query(min_length=1),
    window: str = Query(default="30d", pattern=r"^(7d|30d|90d)$"),
    request: Request = None,
) -> SnapshotDelta:
    rid = request.state.request_id
    days = int(window[:-1])
    return SnapshotDelta(
        current_snapshot=date.today(),
        previous_snapshot=date.today() - timedelta(days=days),
        deltas={"reference_signal": 0.0},
        request_id=rid,
    )


@app.post("/api/v1/assistant", response_model=AssistantResponse)
def assistant(payload: AssistantRequest, request: Request = None) -> AssistantResponse:
    rid = request.state.request_id
    _score(payload.entity_id, rid)  # authoritative context is derived server-side
    return AssistantResponse(
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
