from datetime import date

import pytest
from pydantic import ValidationError

from platform_core.contracts.models import AssistantRequest, LineageMetadata
from scenarios.churn.contracts import ChurnFeatureSnapshot


def test_lineage_requires_real_provenance() -> None:
    data = {
        "git_sha": "abcdef1",
        "workflow_run_id": "run-1",
        "source_dataset": "telco_customer_churn_v1",
        "source_row_count": 7043,
        "feature_schema_version": "churn.features.v1",
        "evaluation_set_hash": "hash",
        "code_version": "0.1.0",
        "environment": "dev",
        "catalog": "mlworkflow_dev",
        "schema_name": "ml",
    }
    assert LineageMetadata(**data).source_row_count == 7043


def test_invalid_feature_domain_is_rejected() -> None:
    with pytest.raises(ValidationError):
        ChurnFeatureSnapshot(
            customer_id="7590-VHVEG",
            snapshot_date=date.today(),
            tenure_months=1,
            session_count_30d=1,
            usage_decay_30d=0,
            open_tickets_30d=0,
            billing_issues_30d=0,
            health_score=1.4,
        )


def test_assistant_does_not_accept_client_score_or_drivers() -> None:
    with pytest.raises(ValidationError):
        AssistantRequest(entity_id="7590-VHVEG", score=0.9, drivers={})


def test_assistant_does_not_accept_client_evidence() -> None:
    with pytest.raises(ValidationError):
        AssistantRequest(entity_id="7590-VHVEG", evidence=[{"source_id": "client"}])
