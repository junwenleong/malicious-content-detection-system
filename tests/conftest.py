"""Shared test configuration and fixtures."""

import os
import sys
import uuid
from typing import Generator

import pytest

# Ensure project root is on sys.path for all tests
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Set up test environment variables BEFORE importing app
os.environ.setdefault("API_KEY", "test-api-key-" + str(uuid.uuid4()))
os.environ.setdefault(
    "HMAC_SECRET", "test-hmac-secret-for-ci-pipeline-minimum-32-chars"
)
os.environ.setdefault("ALLOWED_ORIGINS", '["http://localhost:5173"]')


@pytest.fixture(scope="session", autouse=True)
def setup_test_api_keys() -> None:
    """Set up API keys for all tests."""
    import src.config

    # Ensure api_keys list is populated from api_key
    if (
        src.config.settings.api_key
        and src.config.settings.api_key not in src.config.settings.api_keys
    ):
        src.config.settings.api_keys.append(src.config.settings.api_key)

    # Ensure we have at least one key
    if not src.config.settings.api_keys:
        test_key = "test-api-key-" + str(uuid.uuid4())
        src.config.settings.api_keys = [test_key]


@pytest.fixture(autouse=True)
def reset_rate_limiter() -> Generator[None, None, None]:
    """Reset rate limiter between tests to avoid cross-test contamination."""
    yield
    # Clear rate limiter after each test
    try:
        from api.app import app

        if hasattr(app.state, "auth_rate_limiter"):
            app.state.auth_rate_limiter.requests.clear()
    except (ImportError, AttributeError):
        pass  # Rate limiter not initialized or app not available
