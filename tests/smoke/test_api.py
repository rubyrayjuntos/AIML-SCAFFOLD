from fastapi.testclient import TestClient

from api.app import app

client = TestClient(app)


def test_score_contract_is_server_derived() -> None:
    response = client.get("/api/v1/score", params={"customer_id": "7590-VHVEG"})
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert response.json()["source"] == "/api/v1/score"
    assert response.json()["data"]["entity_id"] == "7590-VHVEG"
    assert "request_id" in response.json()


def test_diff_rejects_unapproved_window() -> None:
    response = client.get("/api/v1/diff", params={"customer_id": "7590-VHVEG", "window": "365d"})
    assert response.status_code == 422


def test_assistant_does_not_trust_client_score() -> None:
    response = client.post("/api/v1/assistant", json={"entity_id": "7590-VHVEG", "score": 0.99})
    assert response.status_code == 422
