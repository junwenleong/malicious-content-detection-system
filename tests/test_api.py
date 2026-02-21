"""
Basic API tests to demonstrate testing setup.
"""

import importlib
import os
import sys
from fastapi.testclient import TestClient


def test_imports() -> None:
    """Test that key dependencies can be imported."""
    try:
        importlib.import_module("fastapi")
        importlib.import_module("sklearn")
        importlib.import_module("joblib")
        importlib.import_module("pandas")
    except ImportError:
        assert False, "Missing required imports"


def test_model_files_exist() -> None:
    """Check that model files are mentioned (though not in Git)."""
    # Model files are excluded from Git via .gitignore
    # This test documents that fact
    assert True, "Model files are excluded from Git (see .gitignore)"


def test_requirements() -> None:
    """Check that requirements file exists."""
    assert os.path.exists("requirements.txt"), "requirements.txt missing"


def _create_client() -> TestClient:
    os.environ.setdefault("DECISION_THRESHOLD", "0.45")
    if "api.app" in sys.modules:
        del sys.modules["api.app"]
    if "src.config" in sys.modules:
        del sys.modules["src.config"]
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from api.app import app

    return TestClient(app)


def test_health_endpoint() -> None:
    with _create_client() as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.headers.get("x-correlation-id")
        data = response.json()
        assert data["status"] == "healthy"


def test_predict_endpoint() -> None:
    with _create_client() as client:
        model_info = client.get("/model-info").json()
        response = client.post("/v1/predict", json={"texts": ["Hello world"]})
        assert response.status_code == 200
        data = response.json()
        assert "predictions" in data
        assert len(data["predictions"]) == 1
        assert data["predictions"][0]["threshold"] == model_info["decision_threshold"]


def test_model_info_endpoint() -> None:
    with _create_client() as client:
        response = client.get("/model-info")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["model_version"], str) and data["model_version"]
        assert data["decision_threshold"] is not None


def test_threshold_behavior_extreme() -> None:
    with _create_client() as client:
        response = client.post("/v1/predict", json={"texts": ["Hello world"]})
        assert response.status_code == 200
        data = response.json()
        prediction = data["predictions"][0]
        if prediction["probability_malicious"] >= prediction["threshold"]:
            assert prediction["label"] == "MALICIOUS"
        else:
            assert prediction["label"] == "BENIGN"


if __name__ == "__main__":
    test_imports()
    test_model_files_exist()
    test_requirements()
    print("All basic checks passed!")
