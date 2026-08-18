from __future__ import annotations

from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class LineageMetadata(BaseModel):
    """Required provenance attached to every candidate model."""

    git_sha: str = Field(min_length=7)
    workflow_run_id: str = Field(min_length=1)
    source_dataset: str = Field(min_length=1)
    source_row_count: int = Field(ge=1)
    feature_schema_version: str = Field(min_length=1)
    evaluation_set_hash: str = Field(min_length=1)
    code_version: str = Field(min_length=1)
    environment: Literal["dev", "test", "prod"]
    catalog: str = Field(min_length=1)
    schema_name: str = Field(min_length=1)


class EvaluationResult(BaseModel):
    task_type: Literal["classification", "regression", "ranking", "forecasting"]
    metrics: dict[str, float]
    passed: bool
    gate_reasons: list[str] = Field(default_factory=list)


class FeatureRegistryEntry(BaseModel):
    """Governed identity for a feature schema and its producing contract."""

    feature_version: str = Field(min_length=1)
    feature_contract: str = Field(min_length=1)
    feature_schema: dict[str, str]
    builder: str = Field(min_length=1)
    source_datasets: list[str] = Field(min_length=1)


class ResponseEnvelope[T](BaseModel):
    request_id: str
    source: str
    version: str
    status: Literal["success", "error"]
    data: T


class ModelCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model_name: str
    model_version: str
    run_id: str
    lineage: LineageMetadata
    evaluation: EvaluationResult


class ScoreResponse(BaseModel):
    entity_id: str
    score: float = Field(ge=0, le=1)
    drivers: dict[str, float | int | str]
    model_version: str
    served_version: str
    feature_version: str
    feature_contract: str
    request_id: str


class SnapshotDelta(BaseModel):
    current_snapshot: date
    previous_snapshot: date
    deltas: dict[str, float | int]
    request_id: str


class AssistantRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    entity_id: str = Field(min_length=1)
    question: str | None = Field(default=None, max_length=2000)


class Evidence(BaseModel):
    source_id: str
    source_type: Literal["note", "ticket", "playbook", "metric"]
    excerpt: str


class AssistantResponse(BaseModel):
    entity_id: str
    risk_explanation: str
    what_changed: str
    recommended_action: str
    evidence: list[Evidence]
    model_version: str
    response_source: Literal["foundry_agent", "deterministic_fallback"]
    request_id: str


class ErrorResponse(BaseModel):
    error: str
    message: str
    request_id: str
    details: dict[str, Any] = Field(default_factory=dict)
