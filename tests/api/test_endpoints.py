"""API contract checks for startup without a generated model artifact."""

from fastapi.testclient import TestClient

from backend.main import create_app


def test_health_reports_degraded_without_bundle(tmp_path):
    with TestClient(create_app(model_dir=tmp_path)) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "degraded"
    assert response.json()["model_loaded"] is False


def test_model_info_does_not_claim_model_metadata_without_bundle(tmp_path):
    with TestClient(create_app(model_dir=tmp_path)) as client:
        response = client.get("/model/info")
    assert response.status_code == 200
    assert response.json()["status"] == "not_loaded"
    assert response.json()["threshold"] is None
    assert response.json()["feature_count"] is None


def test_predict_returns_actionable_503_without_bundle(tmp_path):
    with TestClient(create_app(model_dir=tmp_path)) as client:
        response = client.post("/predict", json={"Destination Port": 80})
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "model_not_loaded"
    assert response.json()["error"]["request_id"]


def test_batch_requires_flow_records(tmp_path):
    with TestClient(create_app(model_dir=tmp_path)) as client:
        response = client.post("/predict/batch", json={"flows": []})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "empty_input"


def test_feature_keys_must_not_collide_after_normalization(tmp_path):
    with TestClient(create_app(model_dir=tmp_path)) as client:
        response = client.post("/predict", json={"Flow Duration": 1, " Flow   Duration ": 2})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "duplicate_feature"
