import csv
import io

from fastapi.testclient import TestClient

from api.app import app


def test_health() -> None:
    with TestClient(app) as client:
        resp = client.get("/health")
        assert resp.status_code == 200, f"Health check failed: {resp.text}"


def test_metrics() -> None:
    with TestClient(app) as client:
        resp = client.get("/metrics")
        assert resp.status_code == 200, f"Metrics check failed: {resp.text}"


def test_predict() -> None:
    data = {"texts": ["Hello world", "You are a bad actor!"]}
    with TestClient(app) as client:
        resp = client.post("/v1/predict", json=data)
        assert resp.status_code == 200, f"/v1/predict failed: {resp.text}"
        json_data = resp.json()
        assert "predictions" in json_data, "No predictions key in response"


def test_batch() -> None:
    csv_content = io.StringIO()
    writer = csv.writer(csv_content)
    writer.writerow(["text"])
    writer.writerow(["Hello world"])
    writer.writerow(["You are a bad actor!"])
    csv_content.seek(0)

    # Encode the string content to bytes for the file upload
    file_content = csv_content.getvalue().encode("utf-8")
    files = {"file": ("test.csv", file_content, "text/csv")}

    with TestClient(app) as client:
        resp = client.post("/v1/batch", files=files)
        assert resp.status_code == 200, f"/v1/batch failed: {resp.text}"


if __name__ == "__main__":
    test_health()
    test_metrics()
    test_predict()
    test_batch()
