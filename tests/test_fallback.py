"""Tests for fallback prediction strategies."""

from src.inference.fallback import FallbackPredictor


class TestFallbackPredictor:
    """Tests for fallback prediction mechanism."""

    def test_fallback_returns_conservative_predictions(self) -> None:
        """Verify fallback returns threshold probabilities for review."""
        fallback = FallbackPredictor()
        threshold = 0.5
        texts = ["test1", "test2", "test3"]

        labels, probs, latency = fallback.predict_safe_fallback(texts, threshold)

        assert len(labels) == 3
        assert all(label == "BENIGN" for label in labels)
        assert all(prob == threshold for prob in probs)
        assert latency == 0.0

    def test_fallback_increments_counter(self) -> None:
        """Verify fallback tracks usage count."""
        fallback = FallbackPredictor()
        initial_count = fallback.fallback_count

        fallback.predict_safe_fallback(["test"], 0.5)
        fallback.predict_safe_fallback(["test"], 0.5)

        assert fallback.fallback_count == initial_count + 2

    def test_fallback_handles_empty_input(self) -> None:
        """Verify fallback handles empty text list."""
        fallback = FallbackPredictor()
        labels, probs, latency = fallback.predict_safe_fallback([], 0.5)

        assert labels == []
        assert probs == []
        assert latency == 0.0

    def test_fallback_uses_provided_threshold(self) -> None:
        """Verify fallback respects provided threshold."""
        fallback = FallbackPredictor()
        custom_threshold = 0.7

        labels, probs, latency = fallback.predict_safe_fallback(
            ["test"], custom_threshold
        )

        assert probs[0] == custom_threshold
