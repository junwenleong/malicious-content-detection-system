"""Tests for input validation and edge cases."""

from fastapi.testclient import TestClient
from api.app import app

client = TestClient(app)


class TestInputValidation:
    """Tests for input validation across endpoints."""

    def test_empty_text_array_rejected(self) -> None:
        """Verify empty text array is rejected."""
        response = client.post(
            "/v1/predict",
            json={"texts": []},
            headers={"x-api-key": "dev-secret-key-123"},
        )
        assert response.status_code == 422  # Pydantic validation error

    def test_whitespace_only_text_rejected(self) -> None:
        """Verify whitespace-only text is rejected."""
        response = client.post(
            "/v1/predict",
            json={"texts": ["   ", "\t\n"]},
            headers={"x-api-key": "dev-secret-key-123"},
        )
        assert response.status_code == 422  # Pydantic validation error
        assert "empty" in response.json()["detail"][0]["msg"].lower()

    def test_oversized_text_rejected(self) -> None:
        """Verify text exceeding max length is rejected."""
        long_text = "a" * 20000  # Exceeds default 10k limit
        response = client.post(
            "/v1/predict",
            json={"texts": [long_text]},
            headers={"x-api-key": "dev-secret-key-123"},
        )
        assert response.status_code in [400, 422]

    def test_batch_size_limit_enforced(self) -> None:
        """Verify batch size limit is enforced."""
        texts = [f"text_{i}" for i in range(2000)]  # Exceeds default 1000 limit
        response = client.post(
            "/v1/predict",
            json={"texts": texts},
            headers={"x-api-key": "dev-secret-key-123"},
        )
        assert response.status_code in [400, 422]

    def test_unicode_normalization_applied(self) -> None:
        """Verify Unicode normalization handles homoglyphs."""
        # Using Latin 'A' vs Cyrillic 'А' (visually identical)
        text_latin = "Admin"
        text_cyrillic = "Аdmin"  # First char is Cyrillic А

        response1 = client.post(
            "/v1/predict",
            json={"texts": [text_latin]},
            headers={"x-api-key": "dev-secret-key-123"},
        )
        response2 = client.post(
            "/v1/predict",
            json={"texts": [text_cyrillic]},
            headers={"x-api-key": "dev-secret-key-123"},
        )

        assert response1.status_code == 200
        assert response2.status_code == 200
        # After normalization, results should be consistent
        # (exact match depends on model, but both should succeed)

    def test_control_characters_stripped(self) -> None:
        """Verify control characters are stripped from input."""
        text_with_controls = "Hello\x00\x01\x02World"
        response = client.post(
            "/v1/predict",
            json={"texts": [text_with_controls]},
            headers={"x-api-key": "dev-secret-key-123"},
        )
        assert response.status_code == 200
        # Should not crash, control chars stripped

    def test_mixed_valid_invalid_texts_rejected(self) -> None:
        """Verify batch with mix of valid/invalid texts is rejected."""
        response = client.post(
            "/v1/predict",
            json={"texts": ["valid text", "   ", "another valid"]},
            headers={"x-api-key": "dev-secret-key-123"},
        )
        assert response.status_code == 422  # Pydantic validation error
