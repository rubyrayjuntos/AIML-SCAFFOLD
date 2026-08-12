from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field


class ChurnFeatureSnapshot(BaseModel):
    customer_id: str
    snapshot_date: date
    tenure_months: int = Field(ge=0)
    session_count_30d: int = Field(ge=0)
    usage_decay_30d: float
    open_tickets_30d: int = Field(ge=0)
    billing_issues_30d: int = Field(ge=0)
    health_score: float = Field(ge=0, le=1)


class ChurnPlaybook(BaseModel):
    action_id: str
    title: str
    description: str
    trigger_conditions: list[str]
    segment_applicability: list[str]
    plan_tier_applicability: list[str]
    expected_outcome: str
    steps: list[str]
    owner: str
    version: str
    effective_at: datetime
