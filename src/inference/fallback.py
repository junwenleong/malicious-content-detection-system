"""Fallback strategies for model inference failures."""

from typing import List, Tuple
import logging

logger = logging.getLogger(__name__)


class FallbackPredictor:
    """Provides fallback predictions when primary model fails.

    This is a safety mechanism to prevent complete service failure.
    Fallback predictions are conservative (mark as REVIEW) to ensure
    human oversight when the primary model is unavailable.
    """

    def __init__(self, default_threshold: float = 0.5):
        """Initialize fallback predictor.

        Args:
            default_threshold: Threshold for fallback decisions
        """
        self.default_threshold = default_threshold
        self.fallback_count = 0

    def predict_safe_fallback(
        self, texts: List[str], threshold: float
    ) -> Tuple[List[str], List[float], float]:
        """Return conservative fallback predictions.

        When the primary model fails, return predictions that trigger
        human review rather than auto-allowing potentially malicious content.

        Args:
            texts: Input texts (used only for count)
            threshold: Decision threshold

        Returns:
            Tuple of (labels, probabilities, latency)
            - All labels are "BENIGN" (to avoid false blocks)
            - All probabilities are at threshold (triggers REVIEW action)
            - Latency is 0.0
        """
        self.fallback_count += 1
        logger.warning(
            f"Using fallback predictions (count: {self.fallback_count}). "
            "Primary model unavailable."
        )

        # Return threshold probability to trigger REVIEW action
        # This ensures human oversight without blocking legitimate traffic
        count = len(texts)
        labels = ["BENIGN"] * count
        probs = [threshold] * count

        return labels, probs, 0.0
