# Implementation Tasks

## Task 1: Create standalone training script
- [x] Extract all code cells from Jupyter notebook
- [x] Create `scripts/train_model.py` with complete training pipeline
- [x] Implement CLI argument parsing (output-dir, random-seed, split ratios)
- [x] Implement structured logging with timestamps
- [x] Implement data loading from HuggingFace
- [x] Implement stratified 70/15/15 data splitting
- [x] Implement GridSearchCV with notebook's exact parameter grid
- [x] Implement isotonic calibration
- [x] Implement threshold optimization via F1 score
- [x] Implement F-beta analysis (F0.5, F1, F2)
- [x] Implement model persistence (joblib .pkl files)
- [x] Implement error handling with actionable messages
- [x] Verify syntax and diagnostics pass

## Task 2: Update dependencies
- [x] Add `datasets>=2.0.0` to `requirements-dev.txt`

## Task 3: Verify script is runnable
- [x] Python AST parse check passes
- [x] Zero diagnostics errors
- [ ] Manual test run (requires HuggingFace dataset download, ~1hr training)
