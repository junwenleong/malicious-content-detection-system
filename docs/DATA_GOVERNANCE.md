# Data Governance & Provenance

## Dataset Information

### Primary Training Dataset

**Name:** Malicious Prompt Detection Dataset (MPDD)
**Source:** Kaggle (mohammedaminejebbar/malicious-prompt-detection-dataset-mpdd)
**License:** CC0 1.0 Universal (Public Domain)
**Access:** https://www.kaggle.com/datasets/mohammedaminejebbar/malicious-prompt-detection-dataset-mpdd
**Size:** 39,234 samples (50/50 balanced: benign/malicious)
**Last Updated:** [Check Kaggle for current version]

### Dataset Composition

- **Benign Samples:** 19,617 (50%)
  - Normal user queries
  - Legitimate system prompts
  - Standard API requests

- **Malicious Samples:** 19,617 (50%)
  - Prompt injection attempts
  - Jailbreak attempts
  - Adversarial inputs
  - Policy violation attempts

### Data Splits

```
Total: 39,234 samples
├── Training: 27,463 (70%)
├── Validation: 5,885 (15%)
└── Test: 5,886 (15%)
```

**Split Strategy:** Stratified random split to maintain class balance across all sets.
**Random Seed:** 42 (reproducible)
**Never Mixed:** Evaluation data never used for threshold tuning or hyperparameter selection.

## Data Handling Practices

### Collection & Storage

- **Collection Method:** Public dataset download via Kaggle API
- **Storage Location:** `data/raw/` (local development), mounted volume (Docker)
- **Retention Policy:** Training data retained for model reproducibility; predictions logged separately
- **Access Control:** Read-only in production; write access restricted to training scripts

### Data Processing Pipeline

1. **Load:** CSV → Pandas DataFrame
2. **Normalize:** Unicode NFKC normalization (removes homoglyphs, control characters)
3. **Validate:** Non-empty text, length constraints (max 10k chars)
4. **Split:** Stratified 70/15/15 train/val/test
5. **Vectorize:** TF-IDF (20k features, 1-2 grams)
6. **Train:** Logistic Regression with GridSearchCV
7. **Calibrate:** Isotonic calibration (5-fold CV)

### Data Quality Checks

- **Null/Missing Values:** None expected in public dataset; validated at load time
- **Duplicates:** Checked during EDA; minimal duplicates expected
- **Class Balance:** Verified at 50/50 split
- **Text Encoding:** UTF-8 validation; NFKC normalization applied
- **Length Distribution:** Checked for outliers; max 10k chars enforced

## Privacy & Security

### What We Log

✅ **Safe to Log:**

- Timestamp, correlation ID, model version
- Predicted label (BENIGN/MALICIOUS)
- Probability score (calibrated)
- Risk level (LOW/MEDIUM/HIGH)
- Recommended action (ALLOW/REVIEW/BLOCK)
- Latency metrics
- API endpoint, HTTP status code

❌ **Never Log:**

- Raw input text (use SHA256 hash for debugging only)
- User identifiers or PII
- Internal file paths or stack traces
- API keys or secrets

### Audit Logging

- **Enabled:** `AUDIT_LOG_ENABLED=true` (production default)
- **Format:** JSON with correlation IDs for traceability
- **Retention:** Follow your organization's data retention policy
- **Access:** Restricted to security and compliance teams

### Data Deletion

- **Training Data:** Retained indefinitely for model reproducibility
- **Prediction Logs:** Delete per your retention policy (e.g., 90 days)
- **Cache:** LRU cache (10k items) cleared on service restart
- **Backups:** Follow your backup retention policy

## Bias & Fairness Considerations

### Known Limitations

1. **Dataset Bias:** Public dataset emphasizes jailbreak/prompt injection patterns
   - May underrepresent other forms of harm
   - May reflect biases in data collection methodology

2. **Language Bias:** Primarily English-language content
   - Performance on non-English text unknown
   - Recommend separate models for other languages

3. **Domain Bias:** Trained on AI/LLM-specific prompts
   - May not generalize to other domains
   - Retrain on domain-specific data for production use

### Fairness Audits

- **Recommended:** Evaluate model performance across demographic groups
- **Methodology:** Stratified evaluation by text characteristics (length, language, domain)
- **Frequency:** Quarterly or after significant data distribution changes
- **Documentation:** Record findings in `docs/FAIRNESS_AUDIT_RESULTS.md`

## Model Versioning & Reproducibility

### Model Artifacts

```
models/
├── malicious_content_detector_calibrated.pkl    (trained model)
├── malicious_content_detector_config.pkl        (config & metadata)
└── README.md                                     (this file)
```

### Integrity Verification

- **SHA256 Checksums:** Verified at startup
- **Version Tracking:** `MODEL_VERSION` in config
- **Training Script:** `scripts/train_model.py` (reproducible with seed=42)
- **Hyperparameters:** Documented in training config

### Retraining Triggers

Retrain the model when:

- False negative rate exceeds 5% on recent data
- Data distribution significantly changes
- New attack patterns emerge
- Quarterly scheduled retraining (best practice)

## Production Data Considerations

### Before Deploying to Production

1. **Evaluate on Your Data:**
   - Train/test on organization-specific dataset
   - Document performance metrics
   - Update MODEL_CARD.md with real-world metrics

2. **Bias Audit:**
   - Evaluate across demographic groups
   - Document fairness findings
   - Establish monitoring thresholds

3. **Compliance Review:**
   - Verify data handling aligns with regulations (GDPR, CCPA, etc.)
   - Document data retention policies
   - Establish audit logging procedures

4. **Operational Readiness:**
   - Set up monitoring and alerting
   - Document runbooks for model failures
   - Establish rollback procedures

## References

- **Training Script:** `scripts/train_model.py`
- **Model Card:** `MODEL_CARD.md`
- **Threat Model:** `docs/THREAT_MODEL.md`
- **Scaling Strategy:** `docs/SCALING_STRATEGY.md`
- **Kaggle Dataset:** https://www.kaggle.com/datasets/mohammedaminejebbar/malicious-prompt-detection-dataset-mpdd
