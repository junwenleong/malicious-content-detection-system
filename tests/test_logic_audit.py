
import threading
import time
import pytest
from src.utils.circuit_breaker import CircuitBreaker
from src.inference.predictor import Predictor
from unittest.mock import MagicMock, patch

def test_circuit_breaker_thread_safety():
    # ... (keep existing)
    breaker = CircuitBreaker(failure_threshold=5, cooldown_seconds=1)
    
    def simulate_failures():
        for _ in range(10):
            breaker.record_failure()
            
    threads = [threading.Thread(target=simulate_failures) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
        
    # Should be open
    assert breaker.state == "open"
    assert breaker.allow_request() is False

@patch('src.utils.circuit_breaker.time')
def test_circuit_breaker_recovery(mock_time):
    mock_time.monotonic.return_value = 100.0
    # cooldown_seconds is min 0.1
    breaker = CircuitBreaker(failure_threshold=1, cooldown_seconds=0.1)
    
    breaker.record_failure()
    # open_until = 100.0 + 0.1 = 100.1
    
    # Check immediate state (within cooldown)
    mock_time.monotonic.return_value = 100.05
    assert breaker.state == "open"
    
    # Move time forward past cooldown
    mock_time.monotonic.return_value = 100.2
    assert breaker.state == "closed"
    assert breaker.allow_request() is True

def test_predictor_empty_input():
    # Create predictor with mocked internals
    predictor = Predictor.__new__(Predictor)
    predictor.model = MagicMock()
    predictor.config = {"positive_class": 1, "optimal_threshold": 0.5}
    predictor.pos_index = 1
    predictor._cache = {}
    predictor._cache_size = 10000
    predictor._lock = __import__("threading").Lock()

    labels, probs, latency = predictor.predict([])
    assert labels == []
    assert probs == []
    assert latency == 0.0

    # Verify model was NOT called
    predictor.model.predict_proba.assert_not_called()
