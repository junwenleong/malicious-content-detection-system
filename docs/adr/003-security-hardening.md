# ADR 003: Security Hardening and Audit Logging

## Status

Accepted

## Context

The system processes untrusted text through a public-facing API. Without proper controls, it's vulnerable to DoS via large payloads, brute-force key guessing, and we'd have no visibility into security events. We also needed to enforce secret quality to prevent weak credentials in production.

## Decision

### Input validation

Enforce `MAX_TEXT_LENGTH` and `MAX_BATCH_ITEMS` at the schema level. Reject oversized requests with 400 before any processing happens.

### Secret management

Use Pydantic validators to enforce minimum complexity (HMAC secret ≥ 32 chars). Support multiple active API keys for zero-downtime rotation. Fail startup if critical secrets are missing in production.

### Audit logging

Centralized `AuditMiddleware` logs all auth events as structured JSON: `{"event": "auth_failure", "client_ip": "...", "reason": "..."}`. Sensitive data (actual keys, raw text) is never logged.

### HMAC signing

Optional HMAC-SHA256 signature verification for request integrity and authenticity. Mitigates replay attacks with a timestamp window.

## Consequences

**Positive:**

- Protected against common DoS vectors (payload size, request volume)
- Security incidents are immediately visible and queryable in logs
- Meets baseline security practices for secret management and auditing

**Negative:**

- Deployments must provide valid, strong secrets — no more empty defaults
- Clients need to handle API keys and potentially HMAC signatures correctly
