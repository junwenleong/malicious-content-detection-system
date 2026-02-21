from typing import Tuple


def policy_decision(probability: float, threshold: float) -> Tuple[str, str]:
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
