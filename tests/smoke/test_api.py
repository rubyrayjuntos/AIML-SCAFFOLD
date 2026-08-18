from fastapi.testclient import TestClient

from api.app import app
from scenarios.churn.databricks_serving import DatabricksServingAdapter

client = TestClient(app)


def test_score_contract_is_server_derived() -> None:
    response = client.get("/api/v1/score", params={"customer_id": "7590-VHVEG"})
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert response.json()["source"] == "/api/v1/score"
    assert response.json()["data"]["entity_id"] == "7590-VHVEG"
    assert "request_id" in response.json()


def test_score_uses_live_adapter_when_configured(monkeypatch) -> None:
    class FakeAdapter:
        def score(self, customer_id: str, request_id: str):
            from platform_core.contracts.models import ScoreResponse

            return ScoreResponse(
                entity_id=customer_id,
                score=0.83,
                drivers={"tenure_months": 1},
                model_version="17",
                served_version="17",
                feature_version="churn.features.v1",
                feature_contract="churn_feature_contract_v1",
                request_id=request_id,
            )

    monkeypatch.setattr(
        DatabricksServingAdapter,
        "from_settings",
        classmethod(lambda cls, settings: FakeAdapter()),
    )
    response = client.get("/api/v1/score", params={"customer_id": "7590-VHVEG"})
    assert response.status_code == 200
    assert response.json()["data"]["score"] == 0.83
    assert response.json()["data"]["served_version"] == "17"


def test_diff_rejects_unapproved_window() -> None:
    response = client.get("/api/v1/diff", params={"customer_id": "7590-VHVEG", "window": "365d"})
    assert response.status_code == 422


def test_assistant_does_not_trust_client_score() -> None:
    response = client.post("/api/v1/assistant", json={"entity_id": "7590-VHVEG", "score": 0.99})
    assert response.status_code == 422
