from fastapi.testclient import TestClient
from fastapi import APIRouter
import sys
import os

# Setup path to import from src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from api.app import app

# Add a route that raises an exception for testing purposes
test_router = APIRouter()


@test_router.get("/force-error")
def force_error() -> None:
    raise ValueError("Intentional test error")


app.include_router(test_router)

client = TestClient(app)


def test_global_exception_handler() -> None:
    response = client.get("/force-error")
    assert response.status_code == 500
    data = response.json()
    
    # RFC 7807 checks
    assert "detail" in data
    assert data["detail"] == "An unexpected error occurred while processing the request."
    assert "title" in data
    assert data["title"] == "Internal Server Error"
    assert "type" in data
    assert data["type"] == "about:blank"
    
    assert "correlation_id" in data
    assert response.headers.get("x-correlation-id") == data["correlation_id"]
