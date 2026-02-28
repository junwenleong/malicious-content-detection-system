from typing import Any, Iterator
import pytest
import joblib
import hashlib
import threading
import numpy as np
from collections import OrderedDict
from unittest.mock import MagicMock, patch

from src.inference.predictor import Predictor


# Mock settings to avoid dependency on actual config/env
@pytest.fixture
def mock_settings() -> Iterator[MagicMock]:
    with patch("src.inference.predictor.settings") as mock:
        mock.model_sha256 = "dummy_hash"
        mock.config_sha256 = "dummy_hash"
        yield mock


def test_checksum_verification_failure(tmp_path: Any, mock_settings: Any) -> None:
    # Create dummy model files
    model_path = tmp_path / "model.pkl"
    config_path = tmp_path / "config.pkl"

    joblib.dump({"classes_": [0, 1]}, model_path)
    joblib.dump({"positive_class": 1}, config_path)

    # Set expected hash to something else (don't need to calculate actual)
    mock_settings.model_sha256 = "wrong_hash"
    mock_settings.config_sha256 = "wrong_hash"

    with pytest.raises(ValueError, match="Integrity check failed"):
        Predictor(str(model_path), str(config_path))


class SimpleModel:
    def __init__(self) -> None:
        self.classes_ = [0, 1]

    def predict_proba(self, X: Any) -> Any:
        return [[0.1, 0.9]] * len(X)


def test_checksum_verification_success(tmp_path: Any, mock_settings: Any) -> None:
    # Create dummy model files
    model_path = tmp_path / "model.pkl"
    config_path = tmp_path / "config.pkl"

    joblib.dump(SimpleModel(), model_path)
    joblib.dump({"positive_class": 1}, config_path)

    # Calculate actual hashes
    with open(model_path, "rb") as f:
        model_hash = hashlib.sha256(f.read()).hexdigest()
    with open(config_path, "rb") as f:
        config_hash = hashlib.sha256(f.read()).hexdigest()

    mock_settings.model_sha256 = model_hash
    mock_settings.config_sha256 = config_hash

    # Should not raise
    predictor = Predictor(str(model_path), str(config_path))
    assert predictor is not None


def test_input_normalization() -> None:
    # Test _normalize_text via predict with mocked model
    with patch.object(Predictor, "__init__", return_value=None):
        predictor = Predictor("dummy", "dummy")
        predictor._lock = threading.Lock()
        predictor._cache = OrderedDict()
        predictor._cache_size = 1000
        predictor._cache_hits = 0
        predictor._cache_misses = 0
        predictor.model = MagicMock()
        predictor.model.predict_proba.return_value = np.array([[0.9, 0.1]])
        predictor.pos_index = 1
        predictor.config = {"optimal_threshold": 0.5}

        # Test NFKC normalization with ligature
        # U+FB01 (fi ligature) -> "fi"
        ligature = "\ufb01"
        normalized = predictor._normalize_text(ligature)
        assert normalized == "fi"

        # Ensure predict calls normalize
        predictor.predict([ligature])
        # The mock should be called with normalized text
        predictor.model.predict_proba.assert_called_with(["fi"])
