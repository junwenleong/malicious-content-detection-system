# Behavioral Abuse Detection for User-Generated API Inputs

## Problem
Detect abusive or policy-violating usage of an API handling user-generated inputs,
under adversarial adaptation, while minimizing false positives, latency, and
operational cost.

## Why this matters
User-generated APIs are constantly probed, evaded, and abused. Traditional
keyword-based filtering fails under adversarial pressure. This project explores
behavioral detection approaches used in real Trust & Safety and Security ML systems.

## Abuse taxonomy
- **Benign**: Normal user requests
- **Abusive**: Policy violations, harmful content (based on harmlessness scores)

## Approach (high-level)
- Prompt-level semantic features (TF-IDF)
- Calibrated logistic regression with threshold tuning
- Session-level behavioral features (future)

## Current Status
✅ Prompt-level abuse classifier trained and calibrated
✅ F-beta threshold optimization complete
✅ Model serialized and ready for API deployment

## Next Steps
- Session-level behavioral feature engineering
- FastAPI endpoint for real-time predictions
- Production deployment pipeline
