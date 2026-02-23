"""Basic sanity tests for core utilities and policy logic."""

import pytest
from src.utils.policy import policy_decision


class TestPolicyDecision:
    """Tests for the centralized policy_decision function."""

    def test_low_probability_allows(self) -> None:
        risk, action = policy_decision(0.1, 0.54)
        assert risk == "LOW"
        assert action == "ALLOW"

    def test_at_threshold_reviews(self) -> None:
        risk, action = policy_decision(0.54, 0.54)
        assert action == "REVIEW"

    def test_above_threshold_plus_margin_blocks(self) -> None:
        risk, action = policy_decision(0.70, 0.54)
        assert action == "BLOCK"

    def test_high_probability_high_risk(self) -> None:
        risk, action = policy_decision(0.90, 0.54)
        assert risk == "HIGH"
        assert action == "BLOCK"

    def test_medium_risk_range(self) -> None:
        risk, _ = policy_decision(0.65, 0.54)
        assert risk == "MEDIUM"

    def test_clamps_negative_probability(self) -> None:
        risk, action = policy_decision(-0.5, 0.54)
        assert risk == "LOW"
        assert action == "ALLOW"

    def test_clamps_probability_above_one(self) -> None:
        risk, action = policy_decision(1.5, 0.54)
        assert risk == "HIGH"
        assert action == "BLOCK"

    def test_zero_probability(self) -> None:
        risk, action = policy_decision(0.0, 0.54)
        assert risk == "LOW"
        assert action == "ALLOW"

    def test_exact_one_probability(self) -> None:
        risk, action = policy_decision(1.0, 0.54)
        assert risk == "HIGH"
        assert action == "BLOCK"

    def test_boundary_between_review_and_block(self) -> None:
        """Above threshold + 0.15, should BLOCK."""
        risk, action = policy_decision(0.70, 0.54)
        assert action == "BLOCK"

    def test_just_below_block_boundary(self) -> None:
        risk, action = policy_decision(0.68, 0.54)
        assert action == "REVIEW"

    def test_extreme_threshold_clamped(self) -> None:
        """Ensure extreme thresholds are clamped to valid range."""
        risk, action = policy_decision(0.5, 0.0)
        # Threshold clamped to 0.01, so 0.5 >= 0.01 + 0.15 → BLOCK
        assert action == "BLOCK"

    def test_negative_threshold_clamped(self) -> None:
        risk, action = policy_decision(0.5, -1.0)
        assert action == "BLOCK"
