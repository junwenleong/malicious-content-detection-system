import time
from src.utils.rate_limiter import RateLimiter


def test_rate_limiter_basic():
    # 5 requests per 1 second
    limiter = RateLimiter(max_requests=5, window_seconds=1)
    client_id = "test_client"

    # First 5 should be allowed
    for _ in range(5):
        assert limiter.is_allowed(client_id) is True

    # 6th should be blocked
    assert limiter.is_allowed(client_id) is False


def test_rate_limiter_window():
    # 2 requests per 0.1 second
    limiter = RateLimiter(max_requests=2, window_seconds=0.1)
    client_id = "test_client"

    assert limiter.is_allowed(client_id) is True
    assert limiter.is_allowed(client_id) is True
    assert limiter.is_allowed(client_id) is False

    # Wait for window to pass
    time.sleep(0.15)

    # Should be allowed again
    assert limiter.is_allowed(client_id) is True


def test_rate_limiter_cleanup():
    # Verify old timestamps are removed
    limiter = RateLimiter(max_requests=10, window_seconds=0.1)
    client_id = "test_client"

    limiter.record_attempt(client_id)
    assert len(limiter.requests[client_id]) == 1

    time.sleep(0.15)

    # Calling is_allowed triggers cleanup
    limiter.is_allowed(client_id)
    # Current call adds 1, but previous 1 should be gone
    assert len(limiter.requests[client_id]) == 1


def test_is_blocked_vs_allowed():
    limiter = RateLimiter(max_requests=1, window_seconds=1)
    client_id = "test_client"

    # is_blocked shouldn't increment count
    assert limiter.is_blocked(client_id) is False
    assert len(limiter.requests[client_id]) == 0

    # is_allowed increments
    assert limiter.is_allowed(client_id) is True
    assert len(limiter.requests[client_id]) == 1

    # Now blocked
    assert limiter.is_blocked(client_id) is True
    assert limiter.is_allowed(client_id) is False


def test_rate_limiter_different_clients():
    """Ensure rate limiting is per-client, not global."""
    limiter = RateLimiter(max_requests=1, window_seconds=1)

    assert limiter.is_allowed("client_a") is True
    assert limiter.is_allowed("client_a") is False  # blocked
    assert limiter.is_allowed("client_b") is True  # different client, allowed
