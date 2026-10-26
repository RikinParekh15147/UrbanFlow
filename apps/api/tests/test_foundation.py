from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_liveness_does_not_claim_dataset_readiness():
    assert client.get("/health").json()["status"] == "ok"
    status = client.get("/api/v1/datasets/status").json()
    assert status["status"] == "not_published"
    assert status["run_id"] is None


def test_unknown_route_has_standard_error_envelope():
    response = client.get("/api/v1/unknown")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "http_error"
