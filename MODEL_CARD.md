# Model Card

## Intended Use
- **Internal Security Tooling:** Prototype for AI testing and red-team workflows.
- Detect prompts that attempt to manipulate systems (prompt injection, jailbreak intent) and other abusive content before it reaches downstream services.
- Provide a calibrated probability, a label (BENIGN/MALICIOUS), and a simple risk/action decision that downstream systems can consume.
- Serve as a trust & safety guardrail in API pipelines and batch processing jobs.

## Out-of-Scope Use
- Not a substitute for comprehensive safety enforcement or human review in high‑risk contexts.
- Not designed to make legal, medical, or financial determinations.
- The demo model is trained on a public dataset that emphasizes jailbreak attempts; it is not meant to be a universal detector for all forms of harm without retraining on enterprise data.

## Performance Metrics

### Demo Dataset Performance
- **ROC AUC**: 0.9882 (clean public dataset)
- **Optimal Threshold**: 0.536 (F1-optimized via PR curve analysis)
- **Calibration**: Sigmoid method, error 0.0055 → 0.0025 (improved calibration)
- **Dataset**: 39,234 samples (perfect 50/50 balance): 27,463 train / 5,885 val / 5,886 test
- **Latency**: ~4ms p50 for single predictions (local test)
- **Throughput**: Scales with CPU cores; lightweight TF-IDF + Logistic Regression

### Important Context
> **The public demo dataset is clean and well-balanced**, resulting in strong metrics (98.82% AUC). This demonstrates the calibration methodology and system architecture.
>
> **Production comparison**: Real-world enterprise datasets with noisier, more ambiguous content typically show:
> - ROC AUC: 85-92% (vs 98.82% demo)
> - Calibration error reduction: 0.18 → 0.04 (vs 0.0055 → 0.0025 demo)
> - More substantial impact from calibration on decision reliability
>
> The system architecture and calibration approach remain valid; evaluate on your organization's data and update this card before production deployment.

## Ethical Considerations
- Bias and fairness: classifiers can reflect biases present in their training data. Use diverse, representative datasets and regularly audit outcomes across segments.
- Transparency: return calibrated probability and threshold so downstream consumers understand the confidence behind decisions.
- Human oversight: route high‑risk cases for review; do not block without appeal paths in high‑impact scenarios.
- Privacy: do not log raw sensitive content at scale; use hashing/sampling where possible. Integrate with your data retention and deletion policies.

## Failure Modes
- Data mismatch: if the production data distribution differs from the demo dataset, recall may drop for certain categories (e.g., direct harm questions vs. jailbreak prompts). Retrain with appropriate corpora.
- Adversarial input: prompt injection patterns evolve. Track false negatives and iterate on training data and features (e.g., n‑grams, character patterns).
- Operational failures: if the model or downstream dependencies fail, the circuit breaker opens to protect the service; rate limiting prevents brute‑force auth attempts. Health and metrics endpoints allow monitoring and fast rollback.
- Confidence miscalibration: thresholds may need re‑tuning when the model or dataset changes. Re‑evaluate calibration and decision thresholds during releases.
