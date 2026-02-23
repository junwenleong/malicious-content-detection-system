"""Tests for global error handling and RFC 7807 Problem Details responses."""

from fastapi import APIRouter
from fastapi.testclient import TestClient
from api.app import app

# Register the test route once but in a controlled way
_test_router_added = False


def _ensure_test_route() -> None:
    """Add a test error route to the app if not already added."""
    global _test_router_added
    if not _test_router_added:
        test_router = APIRouter()

        @test_router.get("/force-error")
        def force_error() -> None:
            raise ValueError("Intentional test error")

        app.include_router(test_router)
        _test_router_added = True


def test_global_exception_handler() -> None:
    _ensure_test_route()
    client = TestClient(app)
    response = client.get("/force-error")
    assert response.status_code == 500
    data = response.json()

    # RFC 7807 checks
    assert (
        data["detail"] == "An unexpected error occurred while processing the request."
    )
    assert data["title"] == "Internal Server Error"
    assert data["type"] == "about:blank"
    assert "correlation_id" in data
    assert response.headers.get("x-correlation-id") == data["correlation_id"]
