import pytest

from platform_core.evaluation.gates import compare_candidate, validate_training_contract
from platform_core.lifecycle.aliases import promote_after_approval


def test_mixed_or_wrong_sized_dataset_cannot_pass() -> None:
    decision = validate_training_contract(
        source_row_count=7067,
        minimum_rows=7043,
        disallowed_row_count=24,
        required_source="telco_customer_churn_v1",
        actual_source="telco_customer_churn_v1",
    )
    assert not decision.passed


def test_candidate_gate_requires_configured_improvement() -> None:
    assert not compare_candidate(
        champion_metric=0.80,
        candidate_metric=0.805,
        minimum_improvement=0.01,
    ).passed
    assert compare_candidate(
        champion_metric=0.80,
        candidate_metric=0.81,
        minimum_improvement=0.01,
    ).passed


class FakeAliasClient:
    def __init__(self):
        self.calls = []

    def set_alias(self, model_name: str, alias: str, version: str) -> None:
        self.calls.append((model_name, alias, version))

    def get_alias(self, model_name: str, alias: str) -> str | None:
        return None


def test_promotion_requires_approval_and_sets_alias() -> None:
    client = FakeAliasClient()
    with pytest.raises(PermissionError):
        promote_after_approval(
            client,
            model_name="mlworkflow_dev.ml.churn_classifier",
            candidate_version="2",
            validation_passed=True,
            production_approved=False,
        )
    assert (
        promote_after_approval(
            client,
            model_name="mlworkflow_dev.ml.churn_classifier",
            candidate_version="2",
            validation_passed=True,
            production_approved=True,
        )
        == "2"
    )
    assert client.calls == [("mlworkflow_dev.ml.churn_classifier", "champion", "2")]
