"""Tests for input validation and edge cases."""

import os
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import src.config
from api.app import app


def _create_client() -> TestClient:
    return TestClient(app)


def _key() -> str:
    return src.config.settings.api_keys[0]


class TestInputValidation:
    """Tests for input validation across endpoints."""

    @pytest.mark.integration
    def test_empty_text_array_rejected(self) -> None:
        """Verify empty text array is rejected."""
        with _create_client() as client:
            response = client.post(
                "/v1/predict",
                json={"texts": []},
                headers={"x-api-key": _key()},
            )
        assert response.status_code == 422

    @pytest.mark.integration
    def test_whitespace_only_text_rejected(self) -> None:
        """Verify whitespace-only text is rejected."""
        with _create_client() as client:
            response = client.post(
                "/v1/predict",
                json={"texts": ["   ", "\t\n"]},
                headers={"x-api-key": _key()},
            )
        assert response.status_code == 422
        assert "empty" in response.json()["detail"][0]["msg"].lower()

    @pytest.mark.integration
    def test_oversized_text_rejected(self) -> None:
        """Verify text exceeding max length is rejected."""
        long_text = "a" * 20000
        with _create_client() as client:
            response = client.post(
                "/v1/predict",
                json={"texts": [long_text]},
                headers={"x-api-key": _key()},
            )
        assert response.status_code in [400, 422]

    @pytest.mark.integration
    def test_batch_size_limit_enforced(self) -> None:
        """Verify batch size limit is enforced."""
        texts = [f"text_{i}" for i in range(2000)]
        with _create_client() as client:
            response = client.post(
                "/v1/predict",
                json={"texts": texts},
                headers={"x-api-key": _key()},
            )
        assert response.status_code in [400, 422]

    @pytest.mark.integration
    def test_unicode_normalization_applied(self) -> None:
        """Verify Unicode normalization handles homoglyphs."""
        text_latin = "Admin"
        text_cyrillic = "Аdmin"  # First char is Cyrillic А

        with _create_client() as client:
            response1 = client.post(
                "/v1/predict",
                json={"texts": [text_latin]},
                headers={"x-api-key": _key()},
            )
            response2 = client.post(
                "/v1/predict",
                json={"texts": [text_cyrillic]},
                headers={"x-api-key": _key()},
            )

        assert response1.status_code == 200
        assert response2.status_code == 200

    @pytest.mark.integration
    def test_control_characters_stripped(self) -> None:
        """Verify control characters are stripped from input."""
        text_with_controls = "Hello\x00\x01\x02World"
        with _create_client() as client:
            response = client.post(
                "/v1/predict",
                json={"texts": [text_with_controls]},
                headers={"x-api-key": _key()},
            )
        assert response.status_code == 200

    @pytest.mark.integration
    def test_mixed_valid_invalid_texts_rejected(self) -> None:
        """Verify batch with mix of valid/invalid texts is rejected."""
        with _create_client() as client:
            response = client.post(
                "/v1/predict",
                json={"texts": ["valid text", "   ", "another valid"]},
                headers={"x-api-key": _key()},
            )
        assert response.status_code == 422
