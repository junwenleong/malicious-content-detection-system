from typing import Tuple

# Risk level thresholds (configurable for different deployment scenarios)
_HIGH_RISK_THRESHOLD = 0.85
_MEDIUM_RISK_THRESHOLD = 0.6

# Action decision margins (relative to decision threshold)
_BLOCK_MARGIN = 0.15  # Block if probability >= threshold + margin


def policy_decision(probability: float, threshold: float) -> Tuple[str, str]:
    """Determine risk level and recommended action based on probability and threshold.

    Args:
        probability: Malicious probability score (0.0 to 1.0).
        threshold: Decision threshold for classification.

    Returns:
        Tuple of (risk_level, recommended_action).
    """
    # Clamp probability to valid range for defensive safety
    probability = max(0.0, min(1.0, probability))

    # Clamp threshold to valid range
    threshold = max(0.01, min(0.99, threshold))

    # Determine risk level based on probability
    if probability >= _HIGH_RISK_THRESHOLD:
        risk_level = "HIGH"
    elif probability >= _MEDIUM_RISK_THRESHOLD:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    # Determine action based on threshold and margin
    if probability >= threshold + _BLOCK_MARGIN:
        recommended_action = "BLOCK"
    elif probability >= threshold:
        recommended_action = "REVIEW"
    else:
        recommended_action = "ALLOW"

    return risk_level, recommended_action
