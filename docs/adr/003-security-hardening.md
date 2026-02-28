# ADR 003: Security Hardening and Audit Logging

## Status

Accepted

## Context

The malicious content detection system exposes an API that processes potentially untrusted text. To ensure the system's integrity, availability, and confidentiality, we need to implement robust security controls. Specifically, we need to address:

- Denial of Service (DoS) risks from large payloads.
- Unauthorized access and brute-force attacks.
- Lack of visibility into security-relevant events (audit trail).
- Risk of weak or hardcoded secrets.

## Decision

We have decided to implement the following security measures:

1.  **Strict Input Validation**:
    - Enforce maximum text length (`MAX_TEXT_LENGTH`) and batch size (`MAX_BATCH_ITEMS`) at the API schema level.
    - Reject requests exceeding these limits with `400 Bad Request` before processing.

2.  **Secret Management & Complexity**:
    - Use `pydantic` validators to enforce minimum complexity for critical secrets (e.g., HMAC secret must be >= 32 characters).
    - Support multiple active API keys to allow for zero-downtime key rotation.
    - Fail startup if critical secrets are missing in production.

3.  **Structured Audit Logging**:
    - Implement a centralized `AuditMiddleware` to log all authentication and authorization events.
    - Use structured JSON format for logs to facilitate parsing by log aggregators (e.g., ELK, Splunk).
    - Log format: `{"event": "auth_failure", "client_ip": "...", "reason": "...", ...}`.
    - Ensure sensitive data (like actual API keys) is never logged.

4.  **HMAC Signature Verification**:
    - Provide an optional HMAC-SHA256 signature verification mechanism for clients to prove request integrity and authenticity, mitigating replay attacks.

## Consequences

### Positive

- **Resilience**: The system is protected against common DoS vectors.
- **Observability**: Security incidents (brute force, invalid keys) are immediately visible and queryable in logs.
- **Compliance**: The system meets basic security best practices for secret management and auditing.

### Negative

- **Configuration Complexity**: Deployments must provide valid, strong secrets.
- **Client Overhead**: Clients must handle API keys and potentially HMAC signatures correctly.
