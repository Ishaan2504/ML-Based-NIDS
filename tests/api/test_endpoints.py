"""API contract checks for startup without the NSL-KDD model artifact."""

from fastapi.testclient import TestClient

from backend.main import create_app


def test_health_reports_degraded_without_bundle(tmp_path):
    with TestClient(create_app(model_path=tmp_path / "missing.pkl")) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "degraded"
    assert response.json()["model_loaded"] is False


def test_model_info_does_not_claim_model_metadata_without_bundle(tmp_path):
    with TestClient(create_app(model_path=tmp_path / "missing.pkl")) as client:
        response = client.get("/model/info")
    assert response.status_code == 200
    assert response.json()["status"] == "not_loaded"
    assert response.json()["threshold"] is None
    assert response.json()["feature_count"] is None


def test_predict_returns_actionable_503_without_bundle(tmp_path):
    with TestClient(create_app(model_path=tmp_path / "missing.pkl")) as client:
        response = client.post("/predict", json={"features": {}})
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "model_not_loaded"
    assert response.json()["error"]["request_id"]


def test_batch_requires_flow_records(tmp_path):
    with TestClient(create_app(model_path=tmp_path / "missing.pkl")) as client:
        response = client.post("/predict/batch", json={"flows": []})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_input"


def test_dynamic_localhost_cors_supports_vite_fallback_ports(tmp_path):
    with TestClient(create_app(model_path=tmp_path / "missing.pkl")) as client:
        response = client.options(
            "/health",
            headers={
                "Origin": "http://127.0.0.1:5175",
                "Access-Control-Request-Method": "GET",
            },
        )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:5175"
