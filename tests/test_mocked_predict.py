import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, AsyncMock

from api.app import app
from src.config import settings
from src.api.auth import verify_signature

client = TestClient(app)

@pytest.fixture
def mock_app_state():
    # Save original state
    original_predictor = getattr(app.state, "predictor", None)
    original_breaker = getattr(app.state, "breaker", None)
    original_rate_limiter = getattr(app.state, "rate_limiter", None)
    original_auth_limiter = getattr(app.state, "auth_rate_limiter", None)
    original_metrics = getattr(app.state, "metrics", None)
    
    # Mock predictor
    mock_predictor = MagicMock()
    # apredict is async
    mock_predictor.apredict = AsyncMock()
    mock_predictor.config = {"optimal_threshold": 0.5}
    
    app.state.predictor = mock_predictor
    
    # Mock breaker
    mock_breaker = MagicMock()
    mock_breaker.allow_request.return_value = True
    mock_breaker.record_failure = MagicMock()
    mock_breaker.record_success = MagicMock()
    app.state.breaker = mock_breaker
    
    # Mock rate limiter
    mock_rate_limiter = MagicMock()
    mock_rate_limiter.is_allowed.return_value = True
    app.state.rate_limiter = mock_rate_limiter
    
    # Mock auth limiter
    mock_auth_limiter = MagicMock()
    mock_auth_limiter.is_blocked.return_value = False
    mock_auth_limiter.record_attempt = MagicMock()
    app.state.auth_rate_limiter = mock_auth_limiter

    # Mock metrics
    mock_metrics = MagicMock()
    mock_metrics.record_prediction = MagicMock()
    mock_metrics.record_error = MagicMock()
    app.state.metrics = mock_metrics
    
    yield mock_predictor, mock_breaker
    
    # Restore
    app.state.predictor = original_predictor
    app.state.breaker = original_breaker
    app.state.rate_limiter = original_rate_limiter
    app.state.auth_rate_limiter = original_auth_limiter
    app.state.metrics = original_metrics

def test_predict_endpoint_success(mock_app_state):
    mock_predictor, _ = mock_app_state
    
    # Mock return values for apredict
    # Returns (labels, probs, latency)
    mock_predictor.apredict.return_value = (
        ["BENIGN", "MALICIOUS"], 
        [0.1, 0.9], 
        0.05
    )
    
    payload = {"texts": ["hello", "evil"]}
    # Need API key headers if auth is enabled
    api_key = settings.api_keys[0] if settings.api_keys else "test-key"
    if not settings.api_keys:
        settings.api_keys = [api_key]
        
    headers = {"x-api-key": api_key}
    
    # Mock verify_signature dependency to bypass HMAC check
    app.dependency_overrides[verify_signature] = lambda: None
    
    try:
        response = client.post("/v1/predict", json=payload, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["predictions"]) == 2
        assert data["predictions"][0]["label"] == "BENIGN"
        assert data["predictions"][1]["label"] == "MALICIOUS"
        assert data["predictions"][1]["risk_level"] == "HIGH"
        
        # Verify metadata
        assert data["metadata"]["malicious_count"] == 1
        assert data["metadata"]["benign_count"] == 1
    finally:
        app.dependency_overrides = {}

def test_circuit_breaker_open(mock_app_state):
    _, mock_breaker = mock_app_state
    mock_breaker.allow_request.return_value = False
    
    api_key = settings.api_keys[0] if settings.api_keys else "test-key"
    if not settings.api_keys:
        settings.api_keys = [api_key]
    headers = {"x-api-key": api_key}
    
    app.dependency_overrides[verify_signature] = lambda: None
    
    try:
        response = client.post("/v1/predict", json={"texts": ["test"]}, headers=headers)
        assert response.status_code == 503
        assert "Inference temporarily unavailable" in response.json()["detail"]
    finally:
        app.dependency_overrides = {}

def test_predict_endpoint_validation_error(mock_app_state):
    # Test empty text list
    api_key = settings.api_keys[0] if settings.api_keys else "test-key"
    if not settings.api_keys:
        settings.api_keys = [api_key]
    headers = {"x-api-key": api_key}
    app.dependency_overrides[verify_signature] = lambda: None
    
    try:
        response = client.post("/v1/predict", json={"texts": []}, headers=headers)
        # Pydantic validation catches empty list (min_length=1)
        assert response.status_code == 422
    finally:
        app.dependency_overrides = {}

def test_predict_endpoint_model_error(mock_app_state):
    mock_predictor, mock_breaker = mock_app_state
    mock_predictor.apredict.side_effect = Exception("Model failed")
    
    api_key = settings.api_keys[0] if settings.api_keys else "test-key"
    if not settings.api_keys:
        settings.api_keys = [api_key]
    headers = {"x-api-key": api_key}
    app.dependency_overrides[verify_signature] = lambda: None
    
    try:
        response = client.post("/v1/predict", json={"texts": ["test"]}, headers=headers)
        assert response.status_code == 503
        assert "Inference error" in response.json()["detail"]
        
        # Verify circuit breaker failure recorded
        mock_breaker.record_failure.assert_called_once()
    finally:
        app.dependency_overrides = {}
