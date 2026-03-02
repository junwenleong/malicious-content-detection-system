"""Shared text utilities."""

import hashlib
import re
import unicodedata


def hash_text(value: str) -> str:
    """Generate a SHA256 hash of text for safe logging without exposing content."""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


# Compiled regex for stripping control characters.
# Shared between training and inference to prevent train/serve skew.
_CONTROL_CHAR_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]")


def normalize_text(text: str) -> str:
    """Normalize text to NFKC form, strip control characters, and lowercase.

    This is the single source of truth for text normalization used by both
    the training pipeline (scripts/train_model.py) and the inference pipeline
    (src/inference/predictor.py). Keeping them in sync prevents train/serve skew.

    NFKC normalization converts compatibility characters and homoglyphs
    into their canonical forms, helping prevent evasion attacks.
    Control characters are stripped to prevent injection attacks.
    Lowercasing matches the training preprocessing pipeline.

    Args:
        text: Raw input text

    Returns:
        Normalized text safe for feature extraction
    """
    if not isinstance(text, str):
        return ""
    normalized = unicodedata.normalize("NFKC", text)
    normalized = _CONTROL_CHAR_RE.sub("", normalized)
    return normalized.lower()
