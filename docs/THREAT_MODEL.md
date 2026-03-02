# Threat Model

## System Overview

The Malicious Content Detection System is an internal API service that classifies text inputs as BENIGN or MALICIOUS using a TF-IDF + Logistic Regression pipeline.

## Attacker Assumptions

- **External attacker**: Has network access to the API endpoint (behind reverse proxy/VPN).
- **Authenticated attacker**: Possesses a valid API key (compromised or insider).
- **Automated attacker**: Uses scripts to send high-volume requests.

## Attack Vectors

### 1. Brute-Force API Key Guessing

- **Mitigation**: Auth rate limiter (5 attempts/minute per IP), API key complexity requirements.
- **Residual Risk**: Low. Attacker would need ~10^18 attempts for a 32-char key.

### 2. Denial of Service (DoS)

- **Mitigation**: Rate limiting (configurable per-IP), max text length (10k chars), max batch size (1000 items), max CSV size (10MB), circuit breaker.
- **Residual Risk**: Medium. Single-process architecture limits throughput. See SCALING_STRATEGY.md.

### 3. Model Evasion / Adversarial Input

- **Mitigation**: Unicode NFKC normalization strips homoglyphs and control characters. TF-IDF features are relatively robust to minor perturbations. Training and inference share a single normalization function (`src/utils/text.normalize_text`) to prevent train/serve skew.
- **Residual Risk**: High. Sophisticated adversaries can craft inputs that evade detection. Continuous retraining and monitoring required.

### 4. Model Tampering

- **Mitigation**: SHA256 checksum verification at startup. Read-only filesystem in production Docker.
- **Residual Risk**: Low if deployment follows production hardening guidelines.

### 5. Replay Attacks

- **Mitigation**: Optional HMAC signature verification with 5-minute timestamp window.
- **Residual Risk**: Low when HMAC is enabled.

### 6. Information Leakage

- **Mitigation**: No raw text in logs (hashed), no internal paths in API responses, generic error messages, no stack traces exposed.
- **Residual Risk**: Low.

### 7. Prompt Injection via Batch CSV

- **Mitigation**: MIME type validation, file extension check, content-length limit, CSV column validation, CSV formula injection sanitization (cells starting with `=`, `+`, `-`, `@` are prefixed with `'`), hard row cap (`MAX_BATCH_ITEMS * 100`) to prevent resource exhaustion via oversized uploads.
- **Residual Risk**: Low. CSV parsing is standard library; no code execution from CSV content.

### 8. Metrics Endpoint Information Leakage

- **Mitigation**: `/metrics` and `/model-info` endpoints require API key authentication. Prometheus metrics expose request counts, error rates, and latency — sufficient for an attacker to fingerprint traffic patterns if unauthenticated. `/model-info` exposes model version, threshold, and cache stats useful for adversarial evasion.
- **Residual Risk**: Low when API key is rotated regularly.

## Failure Impact Analysis

| Failure Mode          | Impact                              | Severity | Recovery                        |
| --------------------- | ----------------------------------- | -------- | ------------------------------- |
| Model fails to load   | Service refuses to start            | High     | Fix model files, redeploy       |
| Inference timeout     | 503 returned, circuit breaker opens | Medium   | Auto-recovery after cooldown    |
| Rate limit exhaustion | 429 returned with Retry-After       | Low      | Wait for window reset           |
| Auth compromise       | Unauthorized predictions            | High     | Rotate API keys immediately     |
| Model evasion         | Malicious content passes through    | High     | Retrain model, adjust threshold |
