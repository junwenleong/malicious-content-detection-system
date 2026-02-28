"""Shared test configuration and fixtures."""

import os
import sys
import uuid

import pytest

# Ensure project root is on sys.path for all tests
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


@pytest.fixture(scope="session", autouse=True)
def setup_test_api_keys() -> None:
    """Set up API keys for all tests."""
    import src.config

    # Generate a test key if not already set
    if not src.config.settings.api_keys or "test-api-key" not in str(
        src.config.settings.api_keys
    ):
        test_key = "test-api-key-" + str(uuid.uuid4())
        src.config.settings.api_key = test_key
        src.config.settings.api_keys = [test_key, "dev-secret-key-123"]


@pytest.fixture(autouse=True)
def reset_rate_limiter() -> None:
    """Reset rate limiter between tests to avoid cross-test contamination."""
    yield
    # Clear rate limiter after each test
    try:
        from api.app import app

        if hasattr(app.state, "auth_rate_limiter"):
            app.state.auth_rate_limiter.requests.clear()
    except (ImportError, AttributeError):
        pass  # Rate limiter not initialized or app not available
