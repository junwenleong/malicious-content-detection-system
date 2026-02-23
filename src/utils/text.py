"""Shared text utilities."""

import hashlib


def hash_text(value: str) -> str:
    """Generate a SHA256 hash of text for safe logging without exposing content."""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
