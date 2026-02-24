#!/usr/bin/env python3
"""
Standalone training script for the Malicious Content Detection model.

Extracts the complete training pipeline from the Jupyter notebook into
a runnable script. Only runs when explicitly executed.

Usage:
    python scripts/train_model.py
    python scripts/train_model.py --output-dir models --random-seed 42
    python scripts/train_model.py --help
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
import time
from dataclasses import dataclass, field
from datetime import timedelta

import joblib
from typing import Any

import numpy as np
import pandas as pd
import psutil
from datasets import load_dataset
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    f1_score,
    fbeta_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import GridSearchCV
from sklearn.pipeline import Pipeline

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
@dataclass
class TrainingConfig:
    """Training configuration with defaults matching the notebook."""

    output_dir: str = "models"
    random_state: int = 42

    # Data splits (must sum to 1.0)
    train_size: float = 0.7
    val_size: float = 0.15
    test_size: float = 0.15

    # Memory management
    sample_size: int | None = None  # If set, subsample training data

    # GridSearchCV
    cv_folds: int = 5
    n_jobs: int = -1
    verbose: int = 1

    # Calibration
    calibration_method: str = "isotonic"
    calibration_cv: int = 5

    # Parameter grid (from notebook)
    param_grid: dict[str, list[object]] = field(
        default_factory=lambda: {
            "tfidf__max_features": [5000, 10000, 20000],
            "tfidf__ngram_range": [(1, 1), (1, 2)],
            "tfidf__min_df": [1, 2, 5],
            "tfidf__max_df": [0.8, 0.9, 1.0],
            "lr__C": [0.01, 0.1, 1, 10],
            "lr__solver": ["lbfgs"],
        }
    )

    # Quick mode: reduced parameter grid for faster training
    quick_mode: bool = False
    quick_param_grid: dict[str, list[object]] = field(
        default_factory=lambda: {
            "tfidf__max_features": [20000],
            "tfidf__ngram_range": [(1, 2)],
            "tfidf__min_df": [5],
            "tfidf__max_df": [1.0],
            "lr__C": [10],
            "lr__solver": ["lbfgs"],
        }
    )


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
def setup_logging() -> None:
    """Configure structured logging with timestamps."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


# ---------------------------------------------------------------------------
# Data Loading
# ---------------------------------------------------------------------------
def load_and_split_data(
    config: TrainingConfig,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load HuggingFace dataset and perform stratified 70/15/15 split."""
    logger.info(
        "Loading dataset from HuggingFace (guychuk/benign-malicious-prompt-classification)..."
    )

    try:
        dataset = load_dataset("guychuk/benign-malicious-prompt-classification")
        ds = dataset["train"]
        df = ds.to_pandas()
    except Exception as e:
        raise RuntimeError(
            f"Failed to load dataset: {e}\n"
            "Check your internet connection and HuggingFace access."
        ) from e

    logger.info("Loaded %d samples", len(df))

    # Memory optimization: subsample if requested
    if config.sample_size is not None and config.sample_size < len(df):
        logger.warning(
            "⚠️  SUBSAMPLING: Using %d samples (%.1f%%) to reduce memory usage",
            config.sample_size,
            100 * config.sample_size / len(df),
        )
        # Use stratified sampling via sklearn
        from sklearn.model_selection import train_test_split

        df, _ = train_test_split(
            df,
            train_size=config.sample_size,
            random_state=config.random_state,
            stratify=df["label"],
        )
        logger.info("Subsampled to %d samples", len(df))

    label_dist = df["label"].value_counts(normalize=True).to_dict()
    logger.info("Class distribution: %s", label_dist)

    # Step 1: Train (70%) / Temp (30%)
    train_df, temp_df = train_test_split(
        df,
        test_size=(config.val_size + config.test_size),
        stratify=df["label"],
        random_state=config.random_state,
    )

    # Step 2: Validation (15%) / Test (15%)
    val_df, test_df = train_test_split(
        temp_df,
        test_size=0.5,
        stratify=temp_df["label"],
        random_state=config.random_state,
    )

    logger.info(
        "Split sizes - Train: %d, Val: %d, Test: %d",
        len(train_df),
        len(val_df),
        len(test_df),
    )

    return train_df, val_df, test_df


# ---------------------------------------------------------------------------
# Preprocessing
# ---------------------------------------------------------------------------
def preprocess_text(text: str) -> str:
    """Lowercase text for consistency (matches notebook preprocessing)."""
    return text.lower() if isinstance(text, str) else ""


def prepare_features_labels(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    test_df: pd.DataFrame,
) -> tuple[pd.Series, pd.Series, pd.Series, np.ndarray, np.ndarray, np.ndarray]:
    """Extract and preprocess features and labels from splits."""
    logger.info("Preprocessing text data...")

    train_texts = train_df["prompt"].apply(preprocess_text)
    val_texts = val_df["prompt"].apply(preprocess_text)
    test_texts = test_df["prompt"].apply(preprocess_text)

    y_train = train_df["label"].values
    y_val = val_df["label"].values
    y_test = test_df["label"].values

    logger.info("Train distribution: %s (0=Benign, 1=Malicious)", np.bincount(y_train))
    logger.info("Val distribution: %s", np.bincount(y_val))

    return train_texts, val_texts, test_texts, y_train, y_val, y_test


# ---------------------------------------------------------------------------
# Model Training
# ---------------------------------------------------------------------------
def train_model_with_gridsearch(
    train_texts: pd.Series,
    y_train: np.ndarray,
    config: TrainingConfig,
) -> Pipeline:
    """Train TF-IDF + LogisticRegression pipeline with GridSearchCV."""
    logger.info("=" * 70)
    logger.info("GRID SEARCH HYPERPARAMETER TUNING")
    logger.info("=" * 70)

    pipe = Pipeline(
        [
            ("tfidf", TfidfVectorizer()),
            ("lr", LogisticRegression(max_iter=1000, class_weight="balanced")),
        ]
    )

    # Use quick mode if requested
    param_grid = config.quick_param_grid if config.quick_mode else config.param_grid

    n_combinations = int(np.prod([len(v) for v in param_grid.values()]))
    total_fits = n_combinations * config.cv_folds

    if config.quick_mode:
        logger.info("⚡ QUICK MODE: Using reduced parameter grid")

    logger.info(
        "Parameter combinations: %d × %d-fold CV = %d model fits",
        n_combinations,
        config.cv_folds,
        total_fits,
    )

    # Estimate memory usage
    est_memory_gb = (len(train_texts) * 20000 * 8 * total_fits) / (1024**3)
    logger.info("Estimated peak memory usage: ~%.1f GB", est_memory_gb)

    if est_memory_gb > 32 and not config.quick_mode and config.sample_size is None:
        logger.warning(
            "⚠️  HIGH MEMORY USAGE EXPECTED! Consider using:\n"
            "   --quick (fast training with good params)\n"
            "   --sample-size 50000 (subsample dataset)\n"
            "   --n-jobs 1 (reduce parallelism)"
        )

    logger.info("This may take several minutes to hours depending on hardware...")

    grid = GridSearchCV(
        estimator=pipe,
        param_grid=param_grid,
        scoring="roc_auc",
        cv=config.cv_folds,
        n_jobs=config.n_jobs,
        verbose=config.verbose,
    )

    start = time.monotonic()
    logger.info("Starting GridSearchCV...")
    grid.fit(train_texts, y_train)
    elapsed = time.monotonic() - start

    logger.info("GridSearchCV completed in %s", timedelta(seconds=int(elapsed)))
    logger.info("Best parameters: %s", grid.best_params_)
    logger.info("Best cross-validation score: %.4f", grid.best_score_)

    return grid.best_estimator_


# ---------------------------------------------------------------------------
# Validation (raw model)
# ---------------------------------------------------------------------------
def evaluate_raw_model(
    model: Pipeline,
    val_texts: pd.Series,
    y_val: np.ndarray,
) -> Any:
    """Evaluate the raw (uncalibrated) model on validation set."""
    logger.info("Evaluating raw model on validation set...")
    start = time.monotonic()

    probs_val_raw = model.predict_proba(val_texts)[:, 1]
    roc_auc_raw = roc_auc_score(y_val, probs_val_raw)

    elapsed = time.monotonic() - start
    logger.info("Validation ROC AUC (raw model): %.4f", roc_auc_raw)
    logger.info("Validation evaluation took: %.2f seconds", elapsed)

    return probs_val_raw


# ---------------------------------------------------------------------------
# Calibration
# ---------------------------------------------------------------------------
def calibrate_model(
    base_model: Pipeline,
    train_texts: pd.Series,
    y_train: np.ndarray,
    config: TrainingConfig,
) -> CalibratedClassifierCV:
    """Apply isotonic calibration to the trained model."""
    logger.info("=" * 70)
    logger.info("MODEL CALIBRATION")
    logger.info("=" * 70)
    logger.info(
        "Fitting calibration on training data (%d-fold CV)...", config.calibration_cv
    )

    calibrated = CalibratedClassifierCV(
        base_model,
        method=config.calibration_method,
        cv=config.calibration_cv,
    )

    start = time.monotonic()
    calibrated.fit(train_texts, y_train)
    elapsed = time.monotonic() - start

    logger.info("Calibration fitted successfully in %.2f seconds", elapsed)
    return calibrated


# ---------------------------------------------------------------------------
# Calibration evaluation
# ---------------------------------------------------------------------------
def evaluate_calibration(
    calibrated_model: CalibratedClassifierCV,
    val_texts: pd.Series,
    y_val: np.ndarray,
    test_texts: pd.Series,
    y_test: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Evaluate calibrated model on validation and test sets."""
    probs_val_cal = calibrated_model.predict_proba(val_texts)[:, 1]
    roc_auc_val = roc_auc_score(y_val, probs_val_cal)
    logger.info("Validation ROC AUC (calibrated): %.4f", roc_auc_val)

    # Calibration error on validation
    fraction_pos_val, mean_pred_val = calibration_curve(y_val, probs_val_cal, n_bins=10)
    val_cal_error = float(abs(np.mean(fraction_pos_val - mean_pred_val)))
    logger.info("Validation calibration error (MAE): %.4f", val_cal_error)

    # Test set evaluation
    logger.info("=" * 70)
    logger.info("TEST SET EVALUATION")
    logger.info("=" * 70)

    probs_test = calibrated_model.predict_proba(test_texts)[:, 1]
    roc_auc_test = roc_auc_score(y_test, probs_test)
    logger.info("Test ROC AUC (calibrated): %.4f", roc_auc_test)

    fraction_pos_test, mean_pred_test = calibration_curve(y_test, probs_test, n_bins=10)
    test_cal_error = float(abs(np.mean(fraction_pos_test - mean_pred_test)))
    logger.info("Test calibration error (MAE): %.4f", test_cal_error)

    if abs(test_cal_error - val_cal_error) < 0.05:
        logger.info("✓ Calibration generalizes well to test data")
    else:
        logger.warning("⚠ Calibration performance differs between validation and test")

    return probs_val_cal, probs_test


# ---------------------------------------------------------------------------
# Threshold Optimization
# ---------------------------------------------------------------------------
def optimize_threshold(
    probs_val_cal: np.ndarray,
    y_val: np.ndarray,
) -> tuple[float, dict[str, float]]:
    """Find optimal threshold by maximizing F1 on validation set."""
    logger.info("=" * 70)
    logger.info("THRESHOLD SELECTION FOR DEPLOYMENT")
    logger.info("=" * 70)
    logger.info("Using calibrated probabilities from validation set...")

    # Precision-recall curve
    precision_val, recall_val, thresholds_val = precision_recall_curve(
        y_val,
        probs_val_cal,
        pos_label=1,
    )

    # F1 scores at each threshold
    f1_scores_val = (
        2 * (precision_val * recall_val) / (precision_val + recall_val + 1e-10)
    )

    best_idx = int(f1_scores_val.argmax())
    best_threshold = float(
        thresholds_val[best_idx] if best_idx < len(thresholds_val) else 0.5
    )

    roc_auc = float(roc_auc_score(y_val, probs_val_cal))

    metrics = {
        "threshold": best_threshold,
        "f1_score": float(f1_scores_val[best_idx]),
        "precision": float(precision_val[best_idx]),
        "recall": float(recall_val[best_idx]),
        "roc_auc": roc_auc,
    }

    logger.info("Optimal threshold: %.4f", best_threshold)
    logger.info("F1 Score: %.4f", metrics["f1_score"])
    logger.info("Precision: %.4f", metrics["precision"])
    logger.info("Recall: %.4f", metrics["recall"])
    logger.info("ROC AUC: %.4f", roc_auc)

    return best_threshold, metrics


# ---------------------------------------------------------------------------
# F-Beta Analysis
# ---------------------------------------------------------------------------
def fbeta_analysis(
    probs_val_cal: np.ndarray,
    y_val: np.ndarray,
    probs_test: np.ndarray,
    y_test: np.ndarray,
    best_threshold: float,
) -> None:
    """Run F-beta analysis across thresholds (informational)."""
    logger.info("=" * 70)
    logger.info("F-BETA ANALYSIS (Validation Set)")
    logger.info("=" * 70)

    beta_values = [0.5, 1, 2]
    thresholds = np.linspace(0, 1, 101)

    # Validation set
    optimal_thresholds_val: dict[float, float] = {}
    for beta in beta_values:
        scores = [
            fbeta_score(y_val, (probs_val_cal >= t).astype(int), beta=beta)
            for t in thresholds
        ]
        opt_idx = int(np.argmax(scores))
        optimal_thresholds_val[beta] = float(thresholds[opt_idx])
        logger.info(
            "  F%.1f: threshold = %.3f, score = %.3f",
            beta,
            thresholds[opt_idx],
            scores[opt_idx],
        )

    chosen = optimal_thresholds_val[1]
    logger.info("F1-optimized threshold from validation: %.3f", chosen)
    logger.info("PR-curve selected threshold: %.3f", best_threshold)

    # Test set final evaluation
    logger.info("-" * 50)
    logger.info("FINAL PERFORMANCE ON TEST SET")
    logger.info("-" * 50)

    y_pred_test = (probs_test >= best_threshold).astype(int)
    logger.info("Confusion Matrix:\n%s", confusion_matrix(y_test, y_pred_test))
    logger.info(
        "Classification Report:\n%s",
        classification_report(
            y_test,
            y_pred_test,
            target_names=["benign (0)", "malicious (1)"],
        ),
    )

    # Compare threshold choices
    threshold_options = {
        "F0.5 (precision-focused)": optimal_thresholds_val[0.5],
        "F1 (balanced)": optimal_thresholds_val[1],
        "F2 (recall-focused)": optimal_thresholds_val[2],
        "PR-curve selected": best_threshold,
    }

    for name, thresh in threshold_options.items():
        y_pred = (probs_test >= thresh).astype(int)
        logger.info(
            "%s (threshold=%.3f): P=%.3f R=%.3f F1=%.3f",
            name,
            thresh,
            precision_score(y_test, y_pred),
            recall_score(y_test, y_pred),
            f1_score(y_test, y_pred),
        )


# ---------------------------------------------------------------------------
# Model Persistence
# ---------------------------------------------------------------------------
def save_model_artifacts(
    calibrated_model: CalibratedClassifierCV,
    threshold: float,
    metrics: dict[str, float],
    config: TrainingConfig,
) -> None:
    """Save calibrated model and configuration to disk."""
    logger.info("Saving model artifacts to %s/...", config.output_dir)

    os.makedirs(config.output_dir, exist_ok=True)

    model_path = os.path.join(
        config.output_dir, "malicious_content_detector_calibrated.pkl"
    )
    config_path = os.path.join(
        config.output_dir, "malicious_content_detector_config.pkl"
    )

    try:
        joblib.dump(calibrated_model, model_path)
        logger.info("Saved model to: %s", model_path)

        config_data = {
            "label_mapping": {0: "benign", 1: "malicious"},
            "positive_class": 1,
            "optimal_threshold": threshold,
            "model_version": "1.0",
            "created_date": pd.Timestamp.now().strftime("%Y-%m-%d"),
            "threshold_selection_method": "Validation PR curve (F1)",
            "metrics": metrics,
            "training_config": {
                "random_state": config.random_state,
                "train_size": config.train_size,
                "val_size": config.val_size,
                "test_size": config.test_size,
            },
        }
        joblib.dump(config_data, config_path)
        logger.info("Saved config to: %s", config_path)

    except Exception as e:
        raise RuntimeError(
            f"Failed to save model artifacts: {e}\n"
            f"Check write permissions for {config.output_dir}/"
        ) from e


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Train malicious content detection model",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        epilog="""
Memory-Efficient Training Examples:
  # Quick training with good defaults (recommended for laptops)
  python scripts/train_model.py --quick

  # Subsample dataset to 50k rows
  python scripts/train_model.py --sample-size 50000

  # Reduce parallelism (slower but less memory)
  python scripts/train_model.py --n-jobs 1

  # Combine strategies for very limited memory
  python scripts/train_model.py --quick --sample-size 50000 --n-jobs 1
        """,
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="models",
        help="Directory to save trained model artifacts",
    )
    parser.add_argument(
        "--random-seed",
        type=int,
        default=42,
        help="Random seed for reproducibility",
    )
    parser.add_argument(
        "--train-size",
        type=float,
        default=0.7,
        help="Proportion of data for training (0.0-1.0)",
    )
    parser.add_argument(
        "--val-size",
        type=float,
        default=0.15,
        help="Proportion of data for validation (0.0-1.0)",
    )
    parser.add_argument(
        "--test-size",
        type=float,
        default=0.15,
        help="Proportion of data for testing (0.0-1.0)",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=None,
        help="Subsample dataset to N rows (reduces memory usage)",
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Use reduced parameter grid for faster training (good defaults)",
    )
    parser.add_argument(
        "--n-jobs",
        type=int,
        default=-1,
        help="Number of parallel jobs for GridSearchCV (-1 = all cores, 1 = sequential)",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    """Run the complete training pipeline."""
    args = parse_arguments()
    setup_logging()

    logger.info("=" * 70)
    logger.info("MALICIOUS CONTENT DETECTION - MODEL TRAINING")
    logger.info("=" * 70)

    # Memory warning
    available_gb = psutil.virtual_memory().available / (1024**3)
    logger.info("Available system memory: %.1f GB", available_gb)

    if available_gb < 16 and not (args.quick or args.sample_size):
        logger.warning(
            "⚠️  LOW MEMORY WARNING!\n"
            "   Full training requires ~60GB RAM and may crash your system.\n"
            "   Recommended options for this machine:\n"
            "     --quick (uses good defaults, ~10GB RAM, 10-30 min)\n"
            "     --sample-size 50000 (subsample dataset, ~20GB RAM)\n"
            "     --n-jobs 1 (sequential processing, slower but less memory)\n"
            "   Press Ctrl+C within 5 seconds to cancel..."
        )
        time.sleep(5)

    config = TrainingConfig(
        output_dir=args.output_dir,
        random_state=args.random_seed,
        train_size=args.train_size,
        val_size=args.val_size,
        test_size=args.test_size,
        sample_size=args.sample_size,
        quick_mode=args.quick,
        n_jobs=args.n_jobs,
    )

    # Validate split sizes
    total = config.train_size + config.val_size + config.test_size
    if not np.isclose(total, 1.0):
        logger.error("Train + val + test sizes must sum to 1.0 (got %.2f)", total)
        sys.exit(1)

    # Set random seeds
    np.random.seed(config.random_state)
    logger.info("Random seed: %d", config.random_state)

    pipeline_start = time.monotonic()

    try:
        # 1. Load and split data
        train_df, val_df, test_df = load_and_split_data(config)

        # 2. Prepare features and labels
        train_texts, val_texts, test_texts, y_train, y_val, y_test = (
            prepare_features_labels(train_df, val_df, test_df)
        )

        # 3. Train model with GridSearchCV
        best_model = train_model_with_gridsearch(train_texts, y_train, config)

        # 4. Evaluate raw model
        evaluate_raw_model(best_model, val_texts, y_val)

        # 5. Calibrate model
        calibrated_model = calibrate_model(best_model, train_texts, y_train, config)

        # 6. Evaluate calibration on val + test
        probs_val_cal, probs_test = evaluate_calibration(
            calibrated_model,
            val_texts,
            y_val,
            test_texts,
            y_test,
        )

        # 7. Optimize threshold
        optimal_threshold, metrics = optimize_threshold(probs_val_cal, y_val)

        # 8. F-beta analysis and final test evaluation
        fbeta_analysis(probs_val_cal, y_val, probs_test, y_test, optimal_threshold)

        # 9. Save model artifacts
        save_model_artifacts(calibrated_model, optimal_threshold, metrics, config)

        # 10. Report completion
        total_time = time.monotonic() - pipeline_start
        logger.info("=" * 70)
        logger.info(
            "TRAINING COMPLETED SUCCESSFULLY in %s", timedelta(seconds=int(total_time))
        )
        logger.info("=" * 70)

    except Exception:
        logger.exception("Training failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
