#!/usr/bin/env python
"""Comprehensive test runner to verify all tests pass."""
import sys
import os

project_root = os.path.dirname(__file__)

def test_imports():
    """Test that all necessary imports work."""
    print("\n" + "=" * 60)
    print("1. TESTING IMPORTS")
    print("=" * 60)

    try:
        print("[OK] backend.main imports successfully")
    except Exception as e:
        print(f"[FAIL] backend.main import failed: {e}")
        return False

    try:
        print("[OK] backend.schemas.flow imports successfully")
    except Exception as e:
        print(f"[FAIL] backend.schemas.flow import failed: {e}")
        return False

    try:
        print("[OK] FastAPI TestClient imports successfully")
    except Exception as e:
        print(f"[FAIL] FastAPI TestClient import failed: {e}")
        return False

    try:
        print("[OK] PyYAML imports successfully")
    except Exception as e:
        print(f"[FAIL] PyYAML import failed: {e}")
        return False

    return True

def test_config_files():
    """Test configuration file structure."""
    print("\n" + "=" * 60)
    print("2. TESTING CONFIG FILES")
    print("=" * 60)

    import yaml

    # Test config.yaml
    try:
        config_path = os.path.join(project_root, "config", "config.yaml")
        assert os.path.exists(config_path), f"config.yaml not found at {config_path}"

        with open(config_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)

        assert "project" in cfg, "Missing 'project' key in config.yaml"
        assert "paths" in cfg, "Missing 'paths' key in config.yaml"
        assert "splitting" in cfg, "Missing 'splitting' key in config.yaml"
        assert cfg["splitting"]["train_ratio"] == 0.60, "train_ratio should be 0.60"

        print("[OK] config.yaml structure is correct")
    except Exception as e:
        print(f"[FAIL] config.yaml test failed: {e}")
        return False

    # Test label_map.yaml
    try:
        label_map_path = os.path.join(project_root, "config", "label_map.yaml")
        assert os.path.exists(label_map_path), f"label_map.yaml not found at {label_map_path}"

        with open(label_map_path, "r", encoding="utf-8") as f:
            labels_data = yaml.safe_load(f)

        assert "labels" in labels_data, "Missing 'labels' key"
        assert "BENIGN" in labels_data["labels"], "Missing 'BENIGN' label"
        assert "DDoS" in labels_data["labels"], "Missing 'DDoS' label"

        print("[OK] label_map.yaml structure is correct")
    except Exception as e:
        print(f"[FAIL] label_map.yaml test failed: {e}")
        return False

    return True

def test_api_endpoints():
    """Test API endpoints."""
    print("\n" + "=" * 60)
    print("3. TESTING API ENDPOINTS")
    print("=" * 60)

    from fastapi.testclient import TestClient
    from backend.main import app

    client = TestClient(app)

    # Test health endpoint
    try:
        response = client.get("/health")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data["status"] == "online", f"Expected 'online', got {data['status']}"
        print("[OK] /health endpoint works")
    except Exception as e:
        print(f"[FAIL] /health endpoint failed: {e}")
        return False

    # Test model info endpoint
    try:
        response = client.get("/model/info")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "Sentinel NIDS" in data["model_name"], "Model name should contain 'Sentinel NIDS'"
        print("[OK] /model/info endpoint works")
    except Exception as e:
        print(f"[FAIL] /model/info endpoint failed: {e}")
        return False

    # Test predict benign flow
    try:
        payload = {
            "Destination Port": 80,
            "Flow Duration": 15000,
            "Total Fwd Packets": 2,
            "Total Backward Packets": 2,
        }
        response = client.post("/predict", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data["label"] == "BENIGN", f"Expected 'BENIGN', got {data['label']}"
        assert data["is_malicious"] is False, "Should not be malicious"
        print("[OK] /predict endpoint works for benign traffic")
    except Exception as e:
        print(f"[FAIL] /predict benign test failed: {e}")
        return False

    # Test predict malicious flow
    try:
        payload = {
            "Destination Port": 22,
            "Flow Duration": 2000,
            "Total Fwd Packets": 50,
            "Total Backward Packets": 0,
            "SYN Flag Count": 1,
            "ACK Flag Count": 0,
        }
        response = client.post("/predict", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data["label"] == "MALICIOUS", f"Expected 'MALICIOUS', got {data['label']}"
        assert data["is_malicious"] is True, "Should be malicious"
        print("[OK] /predict endpoint works for malicious traffic")
    except Exception as e:
        print(f"[FAIL] /predict malicious test failed: {e}")
        return False

    # Test batch prediction
    try:
        payload = {
            "flows": [
                {"Destination Port": 80, "Total Fwd Packets": 2},
                {"Destination Port": 21, "Total Fwd Packets": 40},
            ]
        }
        response = client.post("/predict/batch", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data["total_flows"] == 2, f"Expected 2 flows, got {data['total_flows']}"
        assert len(data["predictions"]) == 2, f"Expected 2 predictions, got {len(data['predictions'])}"
        print("[OK] /predict/batch endpoint works")
    except Exception as e:
        print(f"[FAIL] /predict/batch test failed: {e}")
        return False

    # Test explain endpoint
    try:
        payload = {
            "Destination Port": 80,
            "Flow Duration": 50000,
            "Total Fwd Packets": 10,
        }
        response = client.post("/explain", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "top_features" in data, "Missing 'top_features' in response"
        assert len(data["top_features"]) > 0, "Should have feature attributions"
        print("[OK] /explain endpoint works")
    except Exception as e:
        print(f"[FAIL] /explain test failed: {e}")
        return False

    return True

def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("SENTINEL NIDS TEST SUITE")
    print("=" * 60)

    all_passed = True

    # Run import tests
    if not test_imports():
        all_passed = False
        print("\n[FAIL] Import tests failed")
    else:
        print("\n[OK] All imports successful")

    # Run config tests
    if not test_config_files():
        all_passed = False
        print("\n[FAIL] Config tests failed")
    else:
        print("\n[OK] All config tests passed")

    # Run API tests
    if not test_api_endpoints():
        all_passed = False
        print("\n[FAIL] API tests failed")
    else:
        print("\n[OK] All API tests passed")

    # Final summary
    print("\n" + "=" * 60)
    if all_passed:
        print("[OK] ALL TESTS PASSED")
        print("=" * 60)
        return 0
    else:
        print("[FAIL] SOME TESTS FAILED")
        print("=" * 60)
        return 1

if __name__ == "__main__":
    sys.exit(main())
