from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert data["mode"] == "offline-analysis"


def test_model_info_endpoint():
    response = client.get("/model/info")
    assert response.status_code == 200
    data = response.json()
    assert "Sentinel NIDS" in data["model_name"]
    assert data["threshold"] == 0.50
    assert "BENIGN" in data["supported_families"]


def test_predict_single_flow_benign():
    payload = {
        "Destination Port": 80,
        "Flow Duration": 15000,
        "Total Fwd Packets": 2,
        "Total Backward Packets": 2,
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["label"] == "BENIGN"
    assert data["is_malicious"] is False


def test_predict_single_flow_malicious():
    payload = {
        "Destination Port": 22,
        "Flow Duration": 2000,
        "Total Fwd Packets": 50,
        "Total Backward Packets": 0,
        "SYN Flag Count": 1,
        "ACK Flag Count": 0,
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["label"] == "MALICIOUS"
    assert data["is_malicious"] is True


def test_batch_prediction():
    payload = {
        "flows": [
            {"Destination Port": 80, "Total Fwd Packets": 2},
            {"Destination Port": 21, "Total Fwd Packets": 40},
        ]
    }
    response = client.post("/predict/batch", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["total_flows"] == 2
    assert len(data["predictions"]) == 2


def test_explain_flow():
    payload = {
        "Destination Port": 80,
        "Flow Duration": 50000,
        "Total Fwd Packets": 10,
    }
    response = client.post("/explain", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "top_features" in data
    assert len(data["top_features"]) > 0
