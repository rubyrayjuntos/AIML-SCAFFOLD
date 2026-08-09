from platform_core.contracts.models import ScoreResponse
from platform_core.integrations.databricks_serving import DatabricksServingAdapter
from platform_core.settings.config import Settings


class FakeWorkspace:
    def query_features(self, customer_id: str) -> dict[str, object]:
        assert customer_id == "7590-VHVEG"
        return {
            "tenure_months": 1,
            "MonthlyCharges": 29.85,
            "TotalCharges": 29.85,
            "SeniorCitizen": 0,
            "Contract": "Month-to-month",
            "InternetService": "DSL",
            "TechSupport": "No",
        }

    def query_endpoint(self, endpoint: str, features: dict[str, object]) -> dict[str, object]:
        assert endpoint == "churn-model-endpoint"
        assert features["Contract"] == "Month-to-month"
        return {"predictions": [[0.2, 0.8]]}

    def endpoint_version(self, endpoint: str) -> str:
        return "17"


def test_adapter_returns_authoritative_score_and_versions() -> None:
    result = DatabricksServingAdapter(
        workspace=FakeWorkspace(),
        settings=Settings(databricks_sql_warehouse_id="warehouse-1"),
    ).score("7590-VHVEG", "request-1")

    assert isinstance(result, ScoreResponse)
    assert result.score == 0.8
    assert result.model_version == "17"
    assert result.served_version == "17"
    assert result.feature_version == "churn.features.v1"
    assert result.feature_contract == "churn_feature_contract_v1"
