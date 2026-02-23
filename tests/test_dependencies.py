"""Tests for shared FastAPI dependencies."""

import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException

from src.api.dependencies import resolve_threshold


class TestResolveThreshold:
    """Tests for the resolve_threshold dependency."""

    def test_uses_settings_threshold_when_set(self) -> None:
        with patch("src.api.dependencies.settings") as mock_settings:
            mock_settings.decision_threshold = 0.6
            result = resolve_threshold()
            assert result == 0.6

    def test_uses_predictor_config_when_settings_none(self) -> None:
        with patch("src.api.dependencies.settings") as mock_settings:
            mock_settings.decision_threshold = None
            mock_predictor = MagicMock()
            mock_predictor.config = {"optimal_threshold": 0.54}
            result = resolve_threshold(mock_predictor)
            assert result == 0.54

    def test_raises_when_no_threshold_available(self) -> None:
        with patch("src.api.dependencies.settings") as mock_settings:
            mock_settings.decision_threshold = None
            with pytest.raises(HTTPException) as exc_info:
                resolve_threshold(None)
            assert exc_info.value.status_code == 500

    def test_settings_threshold_takes_precedence(self) -> None:
        with patch("src.api.dependencies.settings") as mock_settings:
            mock_settings.decision_threshold = 0.7
            mock_predictor = MagicMock()
            mock_predictor.config = {"optimal_threshold": 0.54}
            result = resolve_threshold(mock_predictor)
            assert result == 0.7
