# Requirements Document

## Introduction

This document specifies requirements for extracting the Jupyter notebook training code into a standalone Python script. Currently, the ML model training pipeline exists only in `notebooks/malicious_content_detection_analysis.ipynb` (1266 lines). Users need the ability to retrain the model without launching Jupyter, enabling automated retraining workflows and CI/CD integration.

## Glossary

- **Training_Script**: The standalone Python script that executes the complete model training pipeline
- **Model_Artifacts**: The output files (.pkl) containing the trained model and configuration
- **Dataset**: The HuggingFace dataset (guychuk/benign-malicious-prompt-classification)
- **Pipeline**: The complete sequence of training operations from data loading to model saving
- **Calibrated_Model**: The logistic regression model with isotonic calibration applied
- **Threshold**: The optimal decision boundary (0.54) determined via F1 score optimization
- **GridSearchCV**: Scikit-learn's hyperparameter tuning mechanism
- **TF-IDF**: Term Frequency-Inverse Document Frequency vectorization method

## Requirements

### Requirement 1: Standalone Training Script Creation

**User Story:** As a developer, I want to execute model training from the command line, so that I can retrain the model without launching Jupyter.

#### Acceptance Criteria

1. THE Training_Script SHALL be executable via `python scripts/train_model.py`
2. THE Training_Script SHALL load the Dataset from HuggingFace without requiring manual intervention
3. THE Training_Script SHALL perform the complete Pipeline including data splitting, vectorization, training, calibration, and threshold optimization
4. THE Training_Script SHALL save Model_Artifacts to the `models/` directory
5. THE Training_Script SHALL log progress information to stdout during execution

### Requirement 2: Data Loading and Preprocessing

**User Story:** As a developer, I want the script to automatically load and preprocess data, so that I don't need to manually prepare datasets.

#### Acceptance Criteria

1. WHEN the Training_Script executes, THE Training_Script SHALL load the Dataset from HuggingFace using the datasets library
2. THE Training_Script SHALL apply 70/15/15 stratified train/validation/test split
3. THE Training_Script SHALL lowercase text during preprocessing
4. THE Training_Script SHALL preserve class balance across all splits
5. THE Training_Script SHALL validate that the Dataset loaded successfully before proceeding

### Requirement 3: Model Training Pipeline

**User Story:** As a developer, I want the script to execute the complete training pipeline, so that I get a production-ready model.

#### Acceptance Criteria

1. THE Training_Script SHALL create a TF-IDF vectorizer with max_features=20000 and ngram_range=(1,2)
2. THE Training_Script SHALL create a Logistic Regression classifier with appropriate hyperparameters
3. THE Training_Script SHALL perform GridSearchCV for hyperparameter tuning using 5-fold cross-validation
4. THE Training_Script SHALL fit the best model on the training set
5. THE Training_Script SHALL evaluate the model on the validation set before calibration

### Requirement 4: Model Calibration

**User Story:** As a developer, I want the model to produce calibrated probabilities, so that confidence scores are reliable.

#### Acceptance Criteria

1. THE Training_Script SHALL apply isotonic calibration using CalibratedClassifierCV
2. THE Training_Script SHALL use 5-fold cross-validation during calibration
3. THE Training_Script SHALL fit the Calibrated_Model on the training set
4. THE Training_Script SHALL generate calibrated probabilities for the validation set
5. THE Training_Script SHALL evaluate calibration quality on the test set

### Requirement 5: Threshold Optimization

**User Story:** As a developer, I want the script to determine the optimal decision threshold, so that the model achieves the best F1 score.

#### Acceptance Criteria

1. THE Training_Script SHALL compute precision-recall curves on the validation set using calibrated probabilities
2. THE Training_Script SHALL calculate F1 scores at each Threshold point
3. THE Training_Script SHALL select the Threshold that maximizes the F1 score
4. THE Training_Script SHALL apply the optimal Threshold to the test set for final evaluation
5. THE Training_Script SHALL log the optimal Threshold value and corresponding F1 score

### Requirement 6: Model Persistence

**User Story:** As a developer, I want the script to save trained models, so that they can be deployed to production.

#### Acceptance Criteria

1. THE Training_Script SHALL save the Calibrated_Model to `models/malicious_content_detector_calibrated.pkl` using joblib
2. THE Training_Script SHALL save configuration including the optimal Threshold to `models/malicious_content_detector_config.pkl`
3. THE Training_Script SHALL verify that Model_Artifacts were written successfully
4. THE Training_Script SHALL log the file paths of saved Model_Artifacts
5. IF model saving fails, THEN THE Training_Script SHALL raise an exception with a descriptive error message

### Requirement 7: Progress Reporting and Logging

**User Story:** As a developer, I want to see training progress, so that I can monitor long-running training jobs.

#### Acceptance Criteria

1. THE Training_Script SHALL log the start of each major Pipeline stage (data loading, training, calibration, etc.)
2. THE Training_Script SHALL log GridSearchCV progress including the number of fits
3. THE Training_Script SHALL log validation metrics (ROC AUC, F1 score, etc.)
4. THE Training_Script SHALL log the total training time upon completion
5. THE Training_Script SHALL use structured logging with timestamps

### Requirement 8: Error Handling

**User Story:** As a developer, I want clear error messages, so that I can troubleshoot training failures.

#### Acceptance Criteria

1. IF the Dataset fails to load, THEN THE Training_Script SHALL raise an exception with connection/authentication guidance
2. IF insufficient memory is available, THEN THE Training_Script SHALL raise an exception with memory requirements
3. IF Model_Artifacts cannot be saved, THEN THE Training_Script SHALL raise an exception with file permission guidance
4. THE Training_Script SHALL validate that required dependencies are installed before execution
5. THE Training_Script SHALL provide actionable error messages for all failure modes

### Requirement 9: Configuration Options

**User Story:** As a developer, I want to customize training parameters, so that I can experiment with different configurations.

#### Acceptance Criteria

1. WHERE command-line arguments are provided, THE Training_Script SHALL accept optional parameters for output directory
2. WHERE command-line arguments are provided, THE Training_Script SHALL accept optional parameters for random seed
3. WHERE command-line arguments are provided, THE Training_Script SHALL accept optional parameters for test split ratios
4. THE Training_Script SHALL use sensible defaults matching the notebook configuration when no arguments are provided
5. THE Training_Script SHALL validate that provided arguments are within acceptable ranges

### Requirement 10: Reproducibility

**User Story:** As a developer, I want reproducible training results, so that I can verify model consistency.

#### Acceptance Criteria

1. THE Training_Script SHALL set random seeds for numpy, scikit-learn, and Python's random module
2. THE Training_Script SHALL use random_state=42 as the default seed value
3. THE Training_Script SHALL log the random seed value used for each training run
4. THE Training_Script SHALL produce identical Model_Artifacts when run with the same seed and data
5. THE Training_Script SHALL document the Python and library versions required for reproducibility

