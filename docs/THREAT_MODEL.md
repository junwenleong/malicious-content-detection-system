# Threat Model

## System Overview

Internal API service that classifies text inputs as BENIGN or MALICIOUS using a TF-IDF + Logistic Regression pipeline. Deployed behind a reverse proxy or VPN in restricted environments.

## Attacker Profiles

- **External attacker:** Has network access to the API endpoint (behind reverse proxy/VPN)
- **Authenticated attacker:** Holds a valid API key (compromised credential or insider)
- **Automated attacker:** Scripts sending high-volume requests

## Attack Vectors

### 1. Brute-Force API Key Guessing

**Mitigation:** Auth rate limiter (5 attempts/minute per IP), API key complexity requirements.

**Residual risk:** Low. A 32-char key has ~10^18 possible combinations.

### 2. Denial of Service

**Mitigation:** Per-IP rate limiting, max text length (10k chars), max batch size (1000 items), max CSV size (10MB), circuit breaker on inference failures.

**Residual risk:** Medium. Single-process architecture has a throughput ceiling. See [SCALING_STRATEGY.md](SCALING_STRATEGY.md) for what changes under load.

### 3. Model Evasion / Adversarial Input

**Mitigation:** Unicode NFKC normalization strips homoglyphs and control characters. TF-IDF features are reasonably robust to minor perturbations. Training and inference share the same normalization function (`src/utils/text.normalize_text`) to prevent train/serve skew.

**Residual risk:** High. Determined adversaries can craft inputs that evade detection. This is an ongoing arms race — continuous retraining and monitoring are necessary.

### 4. Model Tampering

**Mitigation:** SHA256 checksum verification at startup. Read-only filesystem in production Docker containers.

**Residual risk:** Low, assuming production hardening guidelines are followed.

### 5. Replay Attacks

**Mitigation:** Optional HMAC-SHA256 signature verification with a 5-minute timestamp window.

**Residual risk:** Low when HMAC is enabled.

### 6. Information Leakage

**Mitigation:** No raw text in logs (SHA256 hashed only), no internal paths in API responses, generic error messages, no stack traces exposed to clients.

**Residual risk:** Low.

### 7. CSV Injection via Batch Upload

**Mitigation:** MIME type validation, file extension check, content-length limit, CSV column validation, formula injection sanitization (cells starting with `=`, `+`, `-`, `@` get prefixed with `'`), hard row cap to prevent resource exhaustion.

**Residual risk:** Low. CSV parsing uses the standard library with no code execution.

### 8. Metrics Endpoint Fingerprinting

**Mitigation:** `/metrics` and `/model-info` require API key authentication. Without auth, an attacker could fingerprint traffic patterns from request counts and latency data, or use model version and threshold info for targeted evasion.

**Residual risk:** Low with regular key rotation.

## Failure Impact

| Failure               | Impact                              | Severity | Recovery                        |
| --------------------- | ----------------------------------- | -------- | ------------------------------- |
| Model fails to load   | Service refuses to start            | High     | Fix model files, redeploy       |
| Inference timeout     | 503 returned, circuit breaker opens | Medium   | Auto-recovery after cooldown    |
| Rate limit exhaustion | 429 with Retry-After header         | Low      | Wait for window reset           |
| Auth compromise       | Unauthorized predictions            | High     | Rotate API keys immediately     |
| Model evasion         | Malicious content passes through    | High     | Retrain model, adjust threshold |
