"""Verify training and inference text normalization are identical.

This test guards against train/serve skew — the #1 silent failure mode
in ML systems. Both pipelines must use the shared normalize_text function.
"""

import ast

from src.utils.text import normalize_text
from src.inference.predictor import Predictor


def test_predictor_delegates_to_shared_normalize() -> None:
    """Predictor._normalize_text must delegate to src.utils.text.normalize_text.

    We verify this by checking that the predictor's method produces identical
    output to the shared function across a range of adversarial inputs.
    """
    # Create a predictor instance with mocked internals
    predictor = Predictor.__new__(Predictor)

    test_cases = [
        "Hello World",
        "  spaces  ",
        "\ufb01ligature",  # fi ligature → "fi"
        "UPPERCASE",
        "control\x00chars\x07here",
        "",
        "café",
        "ﬁﬂ",  # ligatures
        "①②③",  # circled digits
    ]
    for text in test_cases:
        assert normalize_text(text) == predictor._normalize_text(text), (
            f"Normalization mismatch for {text!r}: "
            f"shared={normalize_text(text)!r}, "
            f"predictor={predictor._normalize_text(text)!r}"
        )


def test_training_script_imports_shared_normalize() -> None:
    """Verify the training script uses the shared normalize_text function.

    Parses the training script AST to confirm it imports from src.utils.text
    rather than reimplementing normalization locally.
    """
    with open("scripts/train_model.py") as f:
        tree = ast.parse(f.read())

    # Find the preprocess_text function and check it imports normalize_text
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "preprocess_text":
            # Check for import of normalize_text inside the function body
            has_import = any(
                isinstance(stmt, ast.ImportFrom)
                and stmt.module == "src.utils.text"
                and any(alias.name == "normalize_text" for alias in stmt.names)
                for stmt in ast.walk(node)
            )
            assert has_import, (
                "preprocess_text must import normalize_text from src.utils.text "
                "to prevent train/serve skew"
            )
            return

    raise AssertionError("preprocess_text function not found in training script")


def test_non_string_input_returns_empty() -> None:
    """normalize_text handles non-string input gracefully."""
    assert normalize_text(123) == ""  # type: ignore[arg-type]
    assert normalize_text(None) == ""  # type: ignore[arg-type]
