import time
from src.utils.circuit_breaker import CircuitBreaker


def test_circuit_breaker_flow() -> None:
    # 3 failures open it
    cb = CircuitBreaker(failure_threshold=3, cooldown_seconds=0.1)

    # Initial state
    assert cb.allow_request() is True

    # 2 failures -> Still closed
    cb.record_failure()
    cb.record_failure()
    assert cb.allow_request() is True

    # 3rd failure -> Open
    cb.record_failure()
    assert cb.allow_request() is False

    # Wait for cooldown
    time.sleep(0.2)

    # Should be allowed (Half-Open or Closed)
    assert cb.allow_request() is True

    # Success resets everything
    cb.record_success()
    assert cb.failure_count == 0


def test_circuit_breaker_reset_behavior() -> None:
    # Test if it resets count after cooldown
    cb = CircuitBreaker(failure_threshold=2, cooldown_seconds=0.1)

    cb.record_failure()
    cb.record_failure()
    assert cb.allow_request() is False

    time.sleep(0.2)

    # Now allowed.
    assert cb.allow_request() is True

    # One failure shouldn't open it immediately (based on current impl)
    cb.record_failure()
    assert cb.allow_request() is True

    # Second failure opens it again
    cb.record_failure()
    assert cb.allow_request() is False


def test_circuit_breaker_half_open_state() -> None:
    """Test that breaker enters half-open after cooldown expires."""
    cb = CircuitBreaker(failure_threshold=2, cooldown_seconds=0.1)

    # Trip the breaker
    cb.record_failure()
    cb.record_failure()
    assert cb.state == "open"

    # Wait for cooldown
    time.sleep(0.15)

    # Should be half-open now
    assert cb.state == "half-open"
    assert cb.allow_request() is True

    # Success should close it
    cb.record_success()
    assert cb.state == "closed"
