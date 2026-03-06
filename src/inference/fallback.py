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

    def __init__(self) -> None:
        self.fallback_count = 0

    def predict_safe_fallback(
        self, texts: List[str], threshold: float
    ) -> Tuple[List[str], List[float], float]:
        """Return conservative fallback predictions.

        When the primary model fails, return predictions that signal
        degraded state to downstream consumers. Labels are UNKNOWN
        (not BENIGN/MALICIOUS) so consumers can route to human review.

        Args:
            texts: Input texts (used only for count)
            threshold: Decision threshold — returned as probability to trigger REVIEW action

        Returns:
            Tuple of (labels, probabilities, latency)
            - All labels are "UNKNOWN" (signals degraded/fallback state)
            - All probabilities are at threshold (triggers REVIEW action)
            - Latency is 0.0
        """
        self.fallback_count += 1
        logger.warning(
            "Using fallback predictions (count: %d). Primary model unavailable.",
            self.fallback_count,
        )

        # Return threshold probability to trigger REVIEW action.
        # Label is UNKNOWN to signal degraded/fallback state to consumers.
        count = len(texts)
        labels = ["UNKNOWN"] * count
        probs = [threshold] * count

        return labels, probs, 0.0
