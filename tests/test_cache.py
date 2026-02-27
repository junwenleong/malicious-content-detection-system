"""Tests for prediction cache functionality."""

import pytest
from src.inference.predictor import Predictor
from src.config import settings


@pytest.fixture
def predictor() -> Predictor:
    """Create a predictor instance for testing."""
    return Predictor(settings.model_path, settings.config_path)


class TestPredictionCache:
    """Tests for LRU cache in predictor."""

    def test_cache_hit_on_repeated_text(self, predictor: Predictor) -> None:
        """Verify cache returns same result for repeated text."""
        text = "This is a test message"

        # First prediction (cache miss)
        labels1, probs1, _ = predictor.predict([text])
        stats1 = predictor.get_cache_stats()

        # Second prediction (cache hit)
        labels2, probs2, _ = predictor.predict([text])
        stats2 = predictor.get_cache_stats()

        assert labels1 == labels2
        assert probs1 == probs2
        assert stats2["cache_hits"] > stats1["cache_hits"]

    def test_cache_miss_on_new_text(self, predictor: Predictor) -> None:
        """Verify cache misses for new text."""
        predictor.clear_cache()

        text1 = "First message"
        text2 = "Second message"

        predictor.predict([text1])
        stats1 = predictor.get_cache_stats()

        predictor.predict([text2])
        stats2 = predictor.get_cache_stats()

        assert stats2["cache_misses"] > stats1["cache_misses"]

    def test_cache_clear(self, predictor: Predictor) -> None:
        """Verify cache clear resets statistics."""
        predictor.predict(["test"])
        predictor.clear_cache()

        stats = predictor.get_cache_stats()
        assert stats["cache_size"] == 0
        assert stats["cache_hits"] == 0
        assert stats["cache_misses"] == 0

    def test_cache_hit_rate_calculation(self, predictor: Predictor) -> None:
        """Verify hit rate is calculated correctly."""
        predictor.clear_cache()

        text = "test message"
        predictor.predict([text])  # Miss
        predictor.predict([text])  # Hit
        predictor.predict([text])  # Hit

        stats = predictor.get_cache_stats()
        assert stats["cache_hits"] == 2
        assert stats["cache_misses"] == 1
        assert stats["hit_rate"] == pytest.approx(2 / 3, rel=0.01)

    def test_cache_eviction_on_overflow(self, predictor: Predictor) -> None:
        """Verify LRU eviction when cache is full."""
        predictor.clear_cache()

        # Fill cache to capacity
        cache_size = predictor._cache_size
        for i in range(cache_size + 100):
            predictor.predict([f"message_{i}"])

        stats = predictor.get_cache_stats()
        assert stats["cache_size"] <= cache_size
