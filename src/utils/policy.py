from typing import Tuple


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

    if probability >= 0.85:
        risk_level = "HIGH"
    elif probability >= 0.6:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    if probability >= threshold + 0.15:
        recommended_action = "BLOCK"
    elif probability >= threshold:
        recommended_action = "REVIEW"
    else:
        recommended_action = "ALLOW"

    return risk_level, recommended_action
