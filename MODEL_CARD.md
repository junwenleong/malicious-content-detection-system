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

- **ROC AUC**: 0.9881 (test set, calibrated model)
- **Optimal Threshold**: 0.536 (F1-optimized on validation set)
- **Test Set Performance** (at threshold 0.536):
  - Precision: 0.98 (malicious class), 0.94 (benign class)
  - Recall: 0.93 (malicious class), 0.98 (benign class)
  - F1-score: 0.96 (both classes)
  - Accuracy: 0.96
- **Calibration**: Isotonic method, error 0.0055 → 0.0025 (55% improvement)
- **Dataset**: 39,234 samples (perfect 50/50 balance): 27,463 train / 5,885 val / 5,886 test
- **Latency**: ~4ms p50 for single predictions (local test)
- **Throughput**: Scales with CPU cores; lightweight TF-IDF + Logistic Regression

### Important Context

> **The public demo dataset is clean and well-balanced**, resulting in strong metrics (98.81% AUC). This demonstrates the calibration methodology and system architecture.
>
> **Production comparison**: Real-world enterprise datasets with noisier, more ambiguous content typically show:
>
> - ROC AUC: 85-92% (vs 98.81% demo)
> - Calibration error reduction: 0.18 → 0.04 (vs 0.0055 → 0.0025 demo)
> - More substantial impact from calibration on decision reliability
>
> The system architecture and calibration approach remain valid; evaluate on your organization's data and update this card before production deployment.

## Ethical Considerations

- Bias and fairness: classifiers can reflect biases present in their training data. Use diverse, representative datasets and regularly audit outcomes across segments.
- Transparency: return calibrated probability and threshold so downstream consumers understand the confidence behind decisions.
- Human oversight: route high‑risk cases for review; do not block without appeal paths in high‑impact scenarios.
- Privacy: do not log raw sensitive content at scale; use hashing/sampling where possible. Integrate with your data retention and deletion policies.

## Bias Evaluation Methodology

Before production deployment, evaluate the model against the following dimensions:

- **Language bias:** The training dataset is primarily English. Evaluate performance on non-English inputs and document degradation. Consider separate models for other languages.
- **Domain bias:** The dataset emphasizes jailbreak/prompt injection patterns. Evaluate false-negative rates on direct harm queries, hate speech, and other harm categories relevant to your deployment context.
- **Length bias:** Evaluate performance across short (<20 tokens), medium, and long (>200 tokens) inputs. TF-IDF features may underperform on very short texts.
- **Adversarial robustness:** Test against Unicode homoglyph substitutions, leetspeak, and whitespace injection. NFKC normalization mitigates many but not all evasion techniques.
- **Threshold sensitivity:** Document precision/recall trade-offs at ±0.05 around the chosen threshold. Ensure the threshold is re-evaluated on your organization's data before deployment.

Document findings in `docs/FAIRNESS_AUDIT_RESULTS.md` before production deployment.

## Failure Modes

- Data mismatch: if the production data distribution differs from the demo dataset, recall may drop for certain categories (e.g., direct harm questions vs. jailbreak prompts). Retrain with appropriate corpora.
- Adversarial input: prompt injection patterns evolve. Track false negatives and iterate on training data and features (e.g., n‑grams, character patterns).
- Operational failures: if the model or downstream dependencies fail, the circuit breaker opens to protect the service; rate limiting prevents brute‑force auth attempts. Health and metrics endpoints allow monitoring and fast rollback.
- Confidence miscalibration: thresholds may need re‑tuning when the model or dataset changes. Re‑evaluate calibration and decision thresholds during releases.
- Fallback state: when the primary model is unavailable, the `FallbackPredictor` returns `UNKNOWN` labels with `is_fallback: true` in the API response. Downstream consumers must handle this state explicitly — do not treat `UNKNOWN` as `BENIGN`.

## Human-in-the-Loop Escalation

The `REVIEW` recommended action signals a prediction in the uncertain zone near the decision threshold. Downstream systems should:

1. Route `REVIEW` items to a human review queue rather than auto-allowing or auto-blocking.
2. Treat `is_fallback: true` responses as `REVIEW` regardless of label — the primary model was unavailable.
3. Establish SLAs for human review turnaround (e.g., 4 hours for `REVIEW`, immediate for `BLOCK`).
4. Feed human review outcomes back into the training pipeline to improve the model over time.
5. Document the escalation path in your organization's operational runbook (`docs/OPERATIONS.md`).
