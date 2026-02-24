# Design Document

## Introduction

This document provides the technical design for extracting the Jupyter notebook training code into a standalone Python script (`scripts/train_model.py`). The script will enable command-line model retraining without requiring Jupyter, supporting automated workflows and CI/CD integration.

## High-Level Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    train_model.py                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │   CLI Args   │  │   Logging    │  │   Config     │    │
│  │   Parser     │  │   Setup      │  │   Manager    │    │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘    │
│         │                  │                  │             │
│         └──────────────────┴──────────────────┘             │
│                            │                                │
│         ┌──────────────────▼──────────────────┐            │
│         │      Training Pipeline Manager      │            │
│         └──────────────────┬──────────────────┘            │
│                            │                                │
│  ┌─────────────────────────┴─────────────────────────┐    │
│  │                                                     │    │
│  ▼                  ▼                  ▼               ▼    │
│ ┌────────┐    ┌──────────┐    ┌──────────┐    ┌─────────┐│
│ │ Data   │    │  Model   │    │Calibrate │    │Threshold││
│ │ Loader │───▶│ Training │───▶│  Model   │───▶│Optimize ││
│ └────────┘    └──────────┘    └──────────┘    └────┬────┘│
│                                                      │     │
│                                                      ▼     │
│                                              ┌──────────┐ │
│                                              │  Model   │ │
│                                              │  Saver   │ │
│                                              └──────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Initialization**: Parse CLI args → Setup logging → Initialize config
2. **Data Loading**: Load HuggingFace dataset → Convert to DataFrame → Split (70/15/15)
3. **Preprocessing**: Lowercase text → Extract features/labels
4. **Training**: GridSearchCV → Fit best model → Evaluate on validation
5. **Calibration**: Apply sigmoid calibration (more stable than isotonic for smaller datasets) → Fit on training set
6. **Threshold Optimization**: Generate PR curve → Find optimal F1 threshold
7. **Persistence**: Save calibrated model → Save config with threshold
8. **Reporting**: Log metrics → Report completion time

## Low-Level Design

### Module Structure

```python
scripts/
└── train_model.py
    ├── Imports
    ├── Constants
    ├── Configuration Classes
    ├── Utility Functions
    ├── Pipeline Functions
    └── Main Entry Point
```

### Key Components

#### 1. Configuration Management

```python
@dataclass
class TrainingConfig:
    """Training configuration with sensible defaults."""
    # Paths
    output_dir: str = "models"

    # Random seed
    random_state: int = 42

    # Data splits
    train_size: float = 0.7
    val_size: float = 0.15
    test_size: float = 0.15

    # TF-IDF parameters (from notebook)
    max_features: int = 20000
    ngram_range: tuple = (1, 2)
    min_df: int = 5
    max_df: float = 1.0

    # Logistic Regression parameters (from notebook)
    C: float = 10.0
    solver: str = "lbfgs"
    max_iter: int = 1000

    # GridSearchCV parameters
    cv_folds: int = 5
    n_jobs: int = -1  # Use all CPUs
    verbose: int = 2

    # Calibration
    # Note: Sigmoid is more stable than isotonic for smaller datasets
    # The demo uses sigmoid; production may benefit from isotonic with larger datasets
    calibration_method: str = "sigmoid"
    calibration_cv: int = 5
```

#### 2. Logging Setup

```python
def setup_logging() -> logging.Logger:
    """Configure structured logging with timestamps."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    return logging.getLogger(__name__)
```

#### 3. Data Loading

```python
def load_and_split_data(
    config: TrainingConfig,
    logger: logging.Logger
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Load dataset from HuggingFace and perform stratified split.

    Returns:
        (train_df, val_df, test_df): DataFrames with 'prompt' and 'label' columns

    Raises:
        RuntimeError: If dataset loading fails
    """
    logger.info("Loading dataset from HuggingFace...")

    try:
        dataset = load_dataset("guychuk/benign-malicious-prompt-classification")
        ds = dataset["train"]
        df = ds.to_pandas()
    except Exception as e:
        raise RuntimeError(
            f"Failed to load dataset: {e}\n"
            "Check internet connection and HuggingFace access."
        )

    logger.info(f"Loaded {len(df)} samples")
    logger.info(f"Class distribution: {df['label'].value_counts(normalize=True).to_dict()}")

    # First split: train (70%) / temp (30%)
    train_df, temp_df = train_test_split(
        df,
        test_size=(config.val_size + config.test_size),
        stratify=df["label"],
        random_state=config.random_state
    )

    # Second split: val (15%) / test (15%)
    val_df, test_df = train_test_split(
        temp_df,
        test_size=0.5,
        stratify=temp_df["label"],
        random_state=config.random_state
    )

    logger.info(f"Split sizes - Train: {len(train_df)}, Val: {len(val_df)}, Test: {len(test_df)}")

    return train_df, val_df, test_df
```

#### 4. Preprocessing

```python
def preprocess_text(text: str) -> str:
    """Lowercase text for consistency."""
    return text.lower() if isinstance(text, str) else ""

def prepare_features_labels(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    test_df: pd.DataFrame,
    logger: logging.Logger
) -> tuple:
    """
    Extract and preprocess features and labels.

    Returns:
        (train_texts, val_texts, test_texts, y_train, y_val, y_test)
    """
    logger.info("Preprocessing text data...")

    train_texts = train_df["prompt"].apply(preprocess_text)
    val_texts = val_df["prompt"].apply(preprocess_text)
    test_texts = test_df["prompt"].apply(preprocess_text)

    y_train = train_df["label"].values
    y_val = val_df["label"].values
    y_test = test_df["label"].values

    logger.info(f"Train distribution: {np.bincount(y_train)} (0=Benign, 1=Malicious)")
    logger.info(f"Val distribution: {np.bincount(y_val)}")

    return train_texts, val_texts, test_texts, y_train, y_val, y_test
```

#### 5. Model Training with GridSearchCV

```python
def train_model_with_gridsearch(
    train_texts: pd.Series,
    y_train: np.ndarray,
    config: TrainingConfig,
    logger: logging.Logger
) -> Pipeline:
    """
    Train model using GridSearchCV for hyperparameter tuning.

    Returns:
        Best fitted pipeline (TF-IDF + LogisticRegression)
    """
    logger.info("=" * 70)
    logger.info("GRID SEARCH HYPERPARAMETER TUNING")
    logger.info("=" * 70)

    # Define pipeline
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer()),
        ('lr', LogisticRegression(random_state=config.random_state))
    ])

    # Parameter grid (from notebook)
    param_grid = {
        'tfidf__max_features': [10000, 20000, 30000],
        'tfidf__ngram_range': [(1, 1), (1, 2), (1, 3)],
        'tfidf__min_df': [2, 5, 10],
        'tfidf__max_df': [0.9, 1.0],
        'lr__C': [1, 10, 100],
        'lr__solver': ['lbfgs', 'liblinear']
    }

    n_combinations = np.prod([len(v) for v in param_grid.values()])
    logger.info(f"Parameter combinations: {n_combinations} × {config.cv_folds}-fold CV")
    logger.info("This may take several minutes to hours depending on hardware...")

    # GridSearchCV
    grid_search = GridSearchCV(
        pipeline,
        param_grid,
        cv=config.cv_folds,
        scoring='roc_auc',
        n_jobs=config.n_jobs,
        verbose=config.verbose
    )

    start_time = time.monotonic()
    logger.info("Starting GridSearchCV...")

    grid_search.fit(train_texts, y_train)

    elapsed = time.monotonic() - start_time
    logger.info(f"GridSearchCV completed in {timedelta(seconds=int(elapsed))}")
    logger.info(f"Best parameters: {grid_search.best_params_}")
    logger.info(f"Best cross-validation score: {grid_search.best_score_:.4f}")

    return grid_search.best_estimator_
```

#### 6. Model Calibration

```python
def calibrate_model(
    base_model: Pipeline,
    train_texts: pd.Series,
    y_train: np.ndarray,
    config: TrainingConfig,
    logger: logging.Logger
) -> CalibratedClassifierCV:
    """
    Apply sigmoid calibration to the trained model.

    Note: Sigmoid calibration is more stable than isotonic for smaller datasets.
    The demo uses a 20% sample, making sigmoid more appropriate.

    Returns:
        Calibrated classifier
    """
    logger.info("Applying sigmoid calibration...")

    calibrated_model = CalibratedClassifierCV(
        base_model,
        method=config.calibration_method,
        cv=config.calibration_cv
    )

    start_time = time.monotonic()
    calibrated_model.fit(train_texts, y_train)
    elapsed = time.monotonic() - start_time

    logger.info(f"Calibration completed in {elapsed:.2f} seconds")

    return calibrated_model
```

#### 7. Threshold Optimization

```python
def optimize_threshold(
    model: CalibratedClassifierCV,
    val_texts: pd.Series,
    y_val: np.ndarray,
    logger: logging.Logger
) -> tuple[float, dict]:
    """
    Find optimal threshold by maximizing F1 score on validation set.

    Returns:
        (optimal_threshold, metrics_dict)
    """
    logger.info("Optimizing decision threshold on validation set...")

    # Get calibrated probabilities
    y_val_proba = model.predict_proba(val_texts)[:, 1]

    # Compute precision-recall curve
    precisions, recalls, thresholds = precision_recall_curve(y_val, y_val_proba)

    # Calculate F1 scores
    f1_scores = 2 * (precisions * recalls) / (precisions + recalls + 1e-10)

    # Find optimal threshold
    optimal_idx = np.argmax(f1_scores)
    optimal_threshold = thresholds[optimal_idx]
    optimal_f1 = f1_scores[optimal_idx]
    optimal_precision = precisions[optimal_idx]
    optimal_recall = recalls[optimal_idx]

    # Compute ROC AUC
    roc_auc = roc_auc_score(y_val, y_val_proba)

    metrics = {
        'threshold': float(optimal_threshold),
        'f1_score': float(optimal_f1),
        'precision': float(optimal_precision),
        'recall': float(optimal_recall),
        'roc_auc': float(roc_auc)
    }

    logger.info(f"Optimal threshold: {optimal_threshold:.4f}")
    logger.info(f"F1 Score: {optimal_f1:.4f}")
    logger.info(f"Precision: {optimal_precision:.4f}")
    logger.info(f"Recall: {optimal_recall:.4f}")
    logger.info(f"ROC AUC: {roc_auc:.4f}")

    return optimal_threshold, metrics
```

#### 8. Model Persistence

```python
def save_model_artifacts(
    model: CalibratedClassifierCV,
    threshold: float,
    metrics: dict,
    config: TrainingConfig,
    logger: logging.Logger
) -> None:
    """
    Save calibrated model and configuration to disk.

    Raises:
        RuntimeError: If saving fails
    """
    logger.info(f"Saving model artifacts to {config.output_dir}/...")

    # Ensure output directory exists
    os.makedirs(config.output_dir, exist_ok=True)

    model_path = os.path.join(config.output_dir, "malicious_content_detector_calibrated.pkl")
    config_path = os.path.join(config.output_dir, "malicious_content_detector_config.pkl")

    try:
        # Save calibrated model
        joblib.dump(model, model_path)
        logger.info(f"Saved model to: {model_path}")

        # Save configuration with threshold and metrics
        config_data = {
            'threshold': threshold,
            'metrics': metrics,
            'training_config': {
                'random_state': config.random_state,
                'train_size': config.train_size,
                'val_size': config.val_size,
                'test_size': config.test_size
            },
            'model_params': model.base_estimator.get_params()
        }
        joblib.dump(config_data, config_path)
        logger.info(f"Saved config to: {config_path}")

    except Exception as e:
        raise RuntimeError(
            f"Failed to save model artifacts: {e}\n"
            f"Check write permissions for {config.output_dir}/"
        )
```

#### 9. CLI Argument Parser

```python
def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Train malicious content detection model",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        '--output-dir',
        type=str,
        default='models',
        help='Directory to save trained model artifacts'
    )

    parser.add_argument(
        '--random-seed',
        type=int,
        default=42,
        help='Random seed for reproducibility'
    )

    parser.add_argument(
        '--train-size',
        type=float,
        default=0.7,
        help='Proportion of data for training (0.0-1.0)'
    )

    parser.add_argument(
        '--val-size',
        type=float,
        default=0.15,
        help='Proportion of data for validation (0.0-1.0)'
    )

    parser.add_argument(
        '--test-size',
        type=float,
        default=0.15,
        help='Proportion of data for testing (0.0-1.0)'
    )

    return parser.parse_args()
```

#### 10. Main Entry Point

```python
def main() -> None:
    """Main training pipeline."""
    # Parse arguments
    args = parse_arguments()

    # Setup logging
    logger = setup_logging()
    logger.info("=" * 70)
    logger.info("MALICIOUS CONTENT DETECTION - MODEL TRAINING")
    logger.info("=" * 70)

    # Initialize configuration
    config = TrainingConfig(
        output_dir=args.output_dir,
        random_state=args.random_seed,
        train_size=args.train_size,
        val_size=args.val_size,
        test_size=args.test_size
    )

    # Validate split sizes
    if not np.isclose(config.train_size + config.val_size + config.test_size, 1.0):
        raise ValueError("Train, val, and test sizes must sum to 1.0")

    # Set random seeds for reproducibility
    np.random.seed(config.random_state)

    start_time = time.monotonic()

    try:
        # 1. Load and split data
        train_df, val_df, test_df = load_and_split_data(config, logger)

        # 2. Prepare features and labels
        train_texts, val_texts, test_texts, y_train, y_val, y_test = \
            prepare_features_labels(train_df, val_df, test_df, logger)

        # 3. Train model with GridSearchCV
        best_model = train_model_with_gridsearch(train_texts, y_train, config, logger)

        # 4. Calibrate model
        calibrated_model = calibrate_model(best_model, train_texts, y_train, config, logger)

        # 5. Optimize threshold
        optimal_threshold, metrics = optimize_threshold(calibrated_model, val_texts, y_val, logger)

        # 6. Save model artifacts
        save_model_artifacts(calibrated_model, optimal_threshold, metrics, config, logger)

        # 7. Report completion
        total_time = time.monotonic() - start_time
        logger.info("=" * 70)
        logger.info(f"TRAINING COMPLETED SUCCESSFULLY in {timedelta(seconds=int(total_time))}")
        logger.info("=" * 70)

    except Exception as e:
        logger.error(f"Training failed: {e}")
        raise


if __name__ == "__main__":
    main()
```

## Error Handling Strategy

### Error Categories

1. **Dataset Loading Errors**
   - Network connectivity issues
   - HuggingFace API failures
   - Authentication problems
   - **Mitigation**: Clear error messages with troubleshooting steps

2. **Memory Errors**
   - Insufficient RAM for large dataset
   - GridSearchCV memory exhaustion
   - **Mitigation**: Document memory requirements, suggest reducing param grid

3. **File I/O Errors**
   - Permission denied for output directory
   - Disk space exhausted
   - **Mitigation**: Check permissions and space before training

4. **Configuration Errors**
   - Invalid split ratios
   - Invalid hyperparameters
   - **Mitigation**: Validate inputs at startup

## Dependencies

All dependencies are already in `requirements-dev.txt`:
- `datasets` (HuggingFace)
- `scikit-learn`
- `joblib`
- `numpy`
- `pandas`

## Testing Strategy

The script can be tested by:
1. Running with default parameters: `python scripts/train_model.py`
2. Verifying output files exist in `models/`
3. Comparing metrics with notebook results
4. Testing with custom parameters: `python scripts/train_model.py --random-seed 123`

## Performance Considerations

- **GridSearchCV**: Most time-consuming step (~1 hour on typical hardware)
- **Parallelization**: Uses all CPU cores by default (`n_jobs=-1`)
- **Memory**: Requires ~8GB RAM for full dataset
- **Disk**: Requires ~500MB for model artifacts

## Future Enhancements

1. Support for custom datasets (CSV input)
2. Hyperparameter tuning via config file
3. Early stopping for GridSearchCV
4. Model comparison (multiple algorithms)
5. Automated test set evaluation
6. MLflow integration for experiment tracking
