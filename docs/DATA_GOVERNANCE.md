# Data Governance & Provenance

## Dataset

**Name:** Malicious Prompt Detection Dataset (MPDD)
**Source:** [Kaggle](https://www.kaggle.com/datasets/mohammedaminejebbar/malicious-prompt-detection-dataset-mpdd)
**License:** CC0 1.0 Universal (Public Domain)
**Size:** 39,234 samples (50/50 balanced)

### Composition

- 19,617 benign samples — normal queries, legitimate system prompts, standard API requests
- 19,617 malicious samples — prompt injection, jailbreak attempts, adversarial inputs, policy violations

### Splits

```
Total: 39,234
├── Training:   27,463 (70%)
├── Validation:  5,885 (15%)
└── Test:        5,886 (15%)
```

Stratified random split (seed=42) to maintain class balance. Evaluation data is never used for threshold tuning or hyperparameter selection.

## Data Processing Pipeline

1. Load CSV into Pandas
2. Unicode NFKC normalization (strips homoglyphs, control characters)
3. Validate non-empty text, enforce length constraints (max 10k chars)
4. Stratified 70/15/15 split
5. TF-IDF vectorization (20k features, 1-2 grams)
6. Logistic Regression with GridSearchCV
7. Isotonic calibration (5-fold CV)

### Quality Checks

- Null/missing values validated at load time
- Duplicates checked during EDA
- Class balance verified at 50/50
- UTF-8 encoding validated, NFKC normalization applied
- Length distribution checked for outliers

## Privacy & Logging

### What gets logged

- Timestamp, correlation ID, model version
- Predicted label, calibrated probability, risk level, recommended action
- Latency metrics, API endpoint, HTTP status code

### What never gets logged

- Raw input text (SHA256 hash only, for debugging)
- User identifiers or PII
- Internal file paths or stack traces
- API keys or secrets

### Audit logging

JSON-structured with correlation IDs. Enabled by default in production (`AUDIT_LOG_ENABLED=true`). Restrict access to security and compliance teams. Follow your org's retention policy for prediction logs (e.g., 90 days). LRU cache (10k items) clears on service restart.

## Bias & Fairness

### Known limitations

1. The dataset emphasizes jailbreak/injection patterns — it may underrepresent other forms of harm
2. Primarily English content — performance on other languages is unknown
3. Trained on AI/LLM-specific prompts — may not generalize to other domains without retraining

### Before production

- Evaluate model performance across demographic groups and text characteristics (length, language, domain)
- Run fairness audits quarterly or after significant data distribution changes
- Document findings before deploying to production

## Model Artifacts

```
models/
├── malicious_content_detector_calibrated.pkl   (trained model)
└── malicious_content_detector_config.pkl       (config & metadata)
```

SHA256 checksums verified at startup. Training is reproducible via `scripts/train_model.py` with seed=42.

### When to retrain

- False negative rate exceeds 5% on recent data
- Data distribution shifts significantly
- New attack patterns emerge that the model misses
- Quarterly as a baseline practice

## Production Checklist

Before deploying with real data:

1. Train and evaluate on your organization's dataset
2. Update [MODEL_CARD.md](../MODEL_CARD.md) with real-world metrics
3. Run a bias audit and document findings
4. Verify data handling aligns with applicable regulations (GDPR, CCPA, etc.)
5. Set up monitoring, alerting, and rollback procedures
