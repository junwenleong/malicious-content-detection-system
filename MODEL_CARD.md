# Model Card

## Intended Use
- Detect prompts that attempt to manipulate systems (prompt injection, jailbreak intent) and other abusive content before it reaches downstream services.
- Provide a calibrated probability, a label (BENIGN/MALICIOUS), and a simple risk/action decision that downstream systems can consume.
- Serve as a trust & safety guardrail in API pipelines and batch processing jobs.

## Out-of-Scope Use
- Not a substitute for comprehensive safety enforcement or human review in high‑risk contexts.
- Not designed to make legal, medical, or financial determinations.
- The demo model is trained on a public dataset that emphasizes jailbreak attempts; it is not meant to be a universal detector for all forms of harm without retraining on enterprise data.

## Performance Metrics
- Latency (measured in CI on the demo build):
  - Single request: ~4 ms (p50 on local test client)
  - Batch of 10: ~3–8 ms (p50 on local test client)
- Throughput depends on CPU cores and process configuration. The service uses lightweight TF‑IDF + Logistic Regression and scales well with multiple workers.
- Classification metrics vary by dataset. Because sensitive training data is replaced with a public dataset for this demo, we do not publish accuracy/precision/recall here. Evaluate on your organization’s data and update this card before production.
- Calibration: probabilities are calibrated (isotonic) so threshold‑based decisions are more reliable than raw model scores.

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

