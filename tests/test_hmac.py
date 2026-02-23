import hmac
import hashlib
import time
import json
import uuid

import pytest
from fastapi.testclient import TestClient
from api.app import app
import src.config


@pytest.fixture
def enable_hmac():
    old_enabled = src.config.settings.hmac_enabled
    old_secret = src.config.settings.hmac_secret
    old_keys = src.config.settings.api_keys

    src.config.settings.hmac_enabled = True
    src.config.settings.hmac_secret = "test-hmac-secret-" + str(uuid.uuid4())
    src.config.settings.api_keys = ["test-key"]

    yield

    src.config.settings.hmac_enabled = old_enabled
    src.config.settings.hmac_secret = old_secret
    src.config.settings.api_keys = old_keys


def test_hmac_enforcement(enable_hmac):
    with TestClient(app) as client:
        # 1. Missing Header
        resp = client.post(
            "/v1/predict", json={"texts": ["foo"]}, headers={"x-api-key": "test-key"}
        )
        assert resp.status_code == 401
        assert "Missing X-Signature" in resp.text

        # 2. Invalid Format
        resp = client.post(
            "/v1/predict",
            json={"texts": ["foo"]},
            headers={"x-api-key": "test-key", "X-Signature": "invalid"},
        )
        assert resp.status_code == 401
        assert "format" in resp.text

        # 3. Valid Signature
        timestamp = int(time.time())
        # Use exact content to ensure signature matches
        # Note: json.dumps adds spaces by default? No, default is compact?
        # TestClient json parameter behavior:
        # json.dumps(data).encode("utf-8")
        # standard json.dumps uses (', ', ': ') separators by default!
        # But TestClient might use defaults.
        # Let's control the content explicitly.
        data = {"texts": ["foo"]}
        content = json.dumps(data).encode("utf-8")

        payload = f"{timestamp}".encode() + content
        test_secret = src.config.settings.hmac_secret
        signature = hmac.new(test_secret.encode(), payload, hashlib.sha256).hexdigest()

        resp = client.post(
            "/v1/predict",
            content=content,
            headers={
                "x-api-key": "test-key",
                "X-Signature": f"{timestamp}:{signature}",
                "Content-Type": "application/json",
            },
        )
        assert resp.status_code == 200, f"Failed: {resp.text}"

        # 4. Expired Timestamp
        old_ts = timestamp - 400
        payload = f"{old_ts}".encode() + content
        test_secret = src.config.settings.hmac_secret
        signature = hmac.new(test_secret.encode(), payload, hashlib.sha256).hexdigest()
        resp = client.post(
            "/v1/predict",
            content=content,
            headers={
                "x-api-key": "test-key",
                "X-Signature": f"{old_ts}:{signature}",
                "Content-Type": "application/json",
            },
        )
        assert resp.status_code == 401
        assert "expired" in resp.text
