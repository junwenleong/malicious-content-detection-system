import requests
import csv
import io

BASE_URL = "http://127.0.0.1:8000"

def test_health():
    resp = requests.get(f"{BASE_URL}/health")
    assert resp.status_code == 200, f"Health check failed: {resp.text}"
    print("✅ /health OK:", resp.json())

def test_metrics():
    resp = requests.get(f"{BASE_URL}/metrics")
    assert resp.status_code == 200, f"Metrics check failed: {resp.text}"
    print("✅ /metrics OK:", resp.json())

def test_predict():
    data = {"texts": ["Hello world", "You are a bad actor!"]}
    resp = requests.post(f"{BASE_URL}/predict", json=data)
    assert resp.status_code == 200, f"/predict failed: {resp.text}"
    json_data = resp.json()
    assert "predictions" in json_data, "No predictions key in response"
    for pred in json_data["predictions"]:
        print(f"Text: {pred['text']}, Label: {pred['label']}, Prob: {pred['probability_malicious']}")
    print("✅ /predict OK")

def test_batch():
    # create a small CSV in memory
    csv_content = io.StringIO()
    writer = csv.writer(csv_content)
    writer.writerow(["text"])
    writer.writerow(["Hello world"])
    writer.writerow(["You are a bad actor!"])
    csv_content.seek(0)

    files = {"file": ("test.csv", csv_content.getvalue(), "text/csv")}
    resp = requests.post(f"{BASE_URL}/batch", files=files)
    assert resp.status_code == 200, f"/batch failed: {resp.text}"
    print("✅ /batch OK, CSV output preview:")
    print(resp.text.splitlines()[:5])  # show first few lines

if __name__ == "__main__":
    test_health()
    test_metrics()
    test_predict()
    test_batch()
    print("🎉 All sanity tests passed!")

