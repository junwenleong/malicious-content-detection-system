import sys
import time
from typing import Generator

import pytest
from fastapi.testclient import TestClient

from api.app import app
from src.config import settings

# Performance Thresholds (ms)
LATENCY_THRESHOLD_SINGLE = 100
LATENCY_THRESHOLD_BATCH = 200


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        yield c


def test_inference_latency_single(client: TestClient) -> None:
    """
    Ensure inference latency is under threshold for single input.
    """
    text = "This is a test sentence to check latency."
    headers = {"x-api-key": settings.api_keys[0]}

    # Warmup
    client.post("/v1/predict", json={"texts": [text]}, headers=headers)

    start_time = time.perf_counter()
    response = client.post("/v1/predict", json={"texts": [text]}, headers=headers)
    end_time = time.perf_counter()

    assert response.status_code == 200

    total_latency_ms = (end_time - start_time) * 1000
    print(f"\nSingle Request Latency: {total_latency_ms:.2f}ms")

    assert total_latency_ms < LATENCY_THRESHOLD_SINGLE, (
        f"Latency too high: {total_latency_ms:.2f}ms > {LATENCY_THRESHOLD_SINGLE}ms"
    )


def test_inference_latency_batch(client: TestClient) -> None:
    """
    Ensure batch processing scales reasonably.
    """
    texts = ["This is sentence number " + str(i) for i in range(10)]
    headers = {"x-api-key": settings.api_keys[0]}

    # Warmup
    client.post("/v1/predict", json={"texts": texts}, headers=headers)

    start_time = time.perf_counter()
    response = client.post("/v1/predict", json={"texts": texts}, headers=headers)
    end_time = time.perf_counter()

    assert response.status_code == 200

    total_latency_ms = (end_time - start_time) * 1000
    print(f"\nBatch (10) Request Latency: {total_latency_ms:.2f}ms")

    assert total_latency_ms < LATENCY_THRESHOLD_BATCH, (
        f"Batch latency too high: {total_latency_ms:.2f}ms > {LATENCY_THRESHOLD_BATCH}ms"
    )


if __name__ == "__main__":
    # Allow running as script
    try:
        pytest.main([__file__, "-v", "-s"])
    except SystemExit as e:
        sys.exit(e.code)
