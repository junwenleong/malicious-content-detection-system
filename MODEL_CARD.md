# Model Card

## Intended Use

Internal security tooling prototype for AI red-teaming and trust & safety workflows. The model detects prompts that try to manipulate systems (prompt injection, jailbreak attempts) and flags them before they reach downstream services.

It returns a calibrated probability, a binary label (BENIGN/MALICIOUS), and a risk-level recommendation (ALLOW/REVIEW/BLOCK) that downstream systems can act on directly.

## Out-of-Scope Use

- Not a replacement for human review in high-stakes contexts.
- Not designed for legal, medical, or financial decisions.
- The demo model focuses on jailbreak/injection patterns — it won't catch every form of harmful content without retraining on broader data.

## Performance

### Demo Dataset

| Metric            | Value                                          |
| ----------------- | ---------------------------------------------- |
| ROC AUC           | 0.9881 (test set, calibrated)                  |
| Threshold         | 0.536 (F1-optimized on validation)             |
| Precision         | 0.98 malicious / 0.94 benign                   |
| Recall            | 0.93 malicious / 0.98 benign                   |
| F1                | 0.96 (both classes)                            |
| Accuracy          | 0.96                                           |
| Calibration error | 0.0055 → 0.0025 (55% improvement via isotonic) |
| Dataset           | 39,234 samples (50/50 balanced)                |
| Latency           | ~4ms p50 single prediction                     |

### Reality Check

The demo dataset is clean and well-separated, which inflates the numbers. On real enterprise data with noisier, more ambiguous content, expect:

- ROC AUC: 85-92%
- Calibration error reduction: 0.18 → 0.04 (much larger absolute improvement)
- More meaningful impact from calibration on decision reliability

The methodology and architecture hold up — just re-evaluate metrics on your own data before going to production.

## Ethical Considerations

- Classifiers inherit biases from their training data. Audit outcomes across different segments regularly.
- We return the calibrated probability and threshold so consumers can see the confidence behind every decision — no black boxes.
- High-risk cases should route to human review. Don't auto-block without an appeal path in high-impact scenarios.
- Raw text is never logged at scale. Use hashing or sampling for audit trails, and follow your org's data retention policies.

## Bias Evaluation

Before production, evaluate the model on these dimensions:

- **Language:** Training data is primarily English. Test non-English inputs and document any degradation.
- **Domain:** The dataset emphasizes jailbreak/injection. Check false-negative rates on direct harm, hate speech, and other categories relevant to your context.
- **Length:** TF-IDF can underperform on very short texts (<20 tokens). Test across short, medium, and long inputs.
- **Adversarial robustness:** Try Unicode homoglyphs, leetspeak, whitespace injection. NFKC normalization handles many of these, but not all.
- **Threshold sensitivity:** Document precision/recall at ±0.05 around the chosen threshold. Re-tune on your data.

## Failure Modes

- **Data mismatch:** If production data looks different from the training set, recall drops — especially for categories the model hasn't seen (e.g., direct harm vs. jailbreaks). Retrain accordingly.
- **Adversarial evolution:** Prompt injection patterns change over time. Track false negatives and iterate on training data.
- **Operational failures:** Circuit breaker opens on repeated inference failures. Rate limiting handles brute-force auth. Health and metrics endpoints give you visibility for fast rollback.
- **Calibration drift:** Thresholds may need re-tuning when the model or data changes. Re-evaluate during releases.
- **Fallback state:** When the primary model is unavailable, `FallbackPredictor` returns `UNKNOWN` with `is_fallback: true`. Downstream consumers must handle this explicitly — never treat `UNKNOWN` as `BENIGN`.

## Human-in-the-Loop Escalation

The `REVIEW` action means the prediction falls in the uncertain zone near the decision boundary. Downstream systems should:

1. Route `REVIEW` items to a human queue — don't auto-allow or auto-block.
2. Treat `is_fallback: true` responses as `REVIEW` regardless of label.
3. Set SLAs for review turnaround (e.g., 4 hours for REVIEW, immediate for BLOCK).
4. Feed human decisions back into the training pipeline to improve the model over time.
5. Document the escalation path in your operational runbook.
