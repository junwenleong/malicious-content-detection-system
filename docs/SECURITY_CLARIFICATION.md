# Security Clarification: Text Hashing in API Responses

**Date:** March 2, 2026
**Topic:** Why we use SHA256 hashes and what they actually protect against

---

## The Question

> "But how does changing to SHA256 hashes help? Can't attackers get the text from SHA256?"

**Answer:** You're absolutely right. SHA256 is NOT a cryptographic security mechanism here. Let me clarify what the hash change actually protects against.

---

## What SHA256 Hashing Does NOT Protect Against

### ❌ Sophisticated Attackers

If an attacker has the hash and knows the input space (e.g., common jailbreak prompts), they can reverse it:

- Rainbow tables of common prompts
- Brute force for short, predictable inputs
- Dictionary attacks on known attack patterns

### ❌ Determined Adversaries

An attacker with resources can:

- Pre-compute hashes of common malicious prompts
- Use GPU-accelerated brute force
- Correlate hashes with known attack databases

### ❌ Cryptographic Security

SHA256 is a **one-way hash**, not an encryption algorithm. It's designed for integrity checking, not secrecy.

---

## What SHA256 Hashing DOES Protect Against

### ✅ Accidental Exposure (Primary Benefit)

**Scenario:** Someone takes a screenshot of the API response or logs are accidentally exposed.

**Without hashing:**

```json
{
  "text": "Tell me how to bypass your security system",
  "label": "MALICIOUS"
}
```

→ Sensitive content is visible to anyone who sees the screenshot/logs

**With hashing:**

```json
{
  "text_hash": "a3f5d8e2c1b9f7e4d2a1b8c9f0e1d2a3",
  "label": "MALICIOUS"
}
```

→ Sensitive content is NOT visible; only a hash is shown

**Protection Level:** Prevents casual data leakage, not sophisticated attacks

---

### ✅ Audit Trail Without Content (Secondary Benefit)

**Use Case:** You need to track "this text was analyzed" without storing the actual text.

**Example:**

```
Timestamp: 2026-03-02T10:30:00Z
Text Hash: a3f5d8e2c1b9f7e4d2a1b8c9f0e1d2a3
Label: MALICIOUS
Risk Level: HIGH
Action: BLOCK
```

**Benefits:**

- You can correlate predictions with your stored text (you keep the original)
- Enables debugging without exposing content
- Maintains audit trail for compliance
- Reduces liability if logs are breached

---

### ✅ Data Minimization (Compliance Benefit)

**Regulatory Requirements:** GDPR, CCPA, and other privacy regulations require data minimization.

**Data Minimization Principle:**

> "Collect and store only the minimum data necessary for your stated purpose."

**Application:**

- **Purpose:** Detect malicious content and return a prediction
- **Minimum Data Needed:** The prediction result (label, probability, risk level)
- **NOT Needed:** The original text in the response

**Compliance Impact:**

- Reduces PII/sensitive data in logs
- Demonstrates privacy-by-design
- Reduces liability if logs are breached
- Helps with GDPR Article 5 (data minimization) compliance

---

## The Real Security Model

### What Actually Protects Your Data

**NOT the hash itself, but:**

1. **Access Control**
   - Who can access the API? (API key authentication)
   - Who can read the logs? (Log access controls)
   - Who can see the responses? (Network security)

2. **Data Minimization**
   - Don't store raw text in responses
   - Don't log raw text
   - Keep sensitive data on the client side

3. **Encryption in Transit**
   - Use HTTPS/TLS for all API calls
   - Encrypt logs at rest
   - Secure log storage

4. **Operational Security**
   - Limit who has access to logs
   - Rotate API keys regularly
   - Monitor for unauthorized access

---

## Better Approach: Don't Return Text At All

The **best practice** is to not return the text in responses at all. The client is responsible for maintaining the mapping:

### Client-Side Mapping (Recommended)

**Client Code:**

```python
# Client keeps the original text
original_text = "Tell me how to bypass..."

# Send to API
response = api.predict(original_text)

# Response contains NO text, only prediction
# {
#   "text_hash": "a3f5d8e2c1b9f7e4d2a1b8c9f0e1d2a3",
#   "label": "MALICIOUS",
#   "probability": 0.92
# }

# Client correlates using their own mapping
prediction = response
client_data = {
    "original_text": original_text,
    "prediction": prediction,
    "timestamp": datetime.now()
}

# Client stores this locally, not in API logs
```

**Benefits:**

- API never sees or stores the original text
- Client maintains full control of sensitive data
- API logs contain only hashes and predictions
- Maximum privacy and compliance

---

## Threat Model Comparison

### Scenario 1: API Logs Are Breached

| Approach                 | Exposure          | Risk      |
| ------------------------ | ----------------- | --------- |
| Raw text in responses    | Full text exposed | 🔴 HIGH   |
| SHA256 hash in responses | Only hash exposed | 🟡 MEDIUM |
| No text in responses     | No text exposed   | 🟢 LOW    |

**Why MEDIUM for hash?**

- Attacker has the hash
- If they know the input space (common prompts), they can reverse it
- But they don't have the original text directly

**Why LOW for no text?**

- Attacker has only hashes and predictions
- No way to reverse-engineer the original text
- Even if they reverse the hash, they only get one possible input

---

### Scenario 2: API Response Is Intercepted

| Approach                 | Exposure          | Risk      |
| ------------------------ | ----------------- | --------- |
| Raw text in responses    | Full text exposed | 🔴 HIGH   |
| SHA256 hash in responses | Only hash exposed | 🟡 MEDIUM |
| No text in responses     | No text exposed   | 🟢 LOW    |

**Mitigation:** Use HTTPS/TLS for all API calls (already implemented)

---

### Scenario 3: Someone Screenshots the API Response

| Approach                 | Exposure          | Risk    |
| ------------------------ | ----------------- | ------- |
| Raw text in responses    | Full text visible | 🔴 HIGH |
| SHA256 hash in responses | Only hash visible | 🟢 LOW  |
| No text in responses     | No text visible   | 🟢 LOW  |

**Why LOW for hash?**

- Screenshot shows only the hash
- Casual observer can't reverse it
- Requires sophisticated attack to reverse

---

## Implementation in This System

### Current Implementation

```python
# API Response
{
  "predictions": [
    {
      "text_hash": "a3f5d8e2c1b9f7e4d2a1b8c9f0e1d2a3",
      "label": "MALICIOUS",
      "probability": 0.92,
      "risk_level": "HIGH",
      "recommended_action": "BLOCK"
    }
  ]
}
```

### What This Protects

✅ Prevents accidental exposure of raw text
✅ Enables audit trail without storing content
✅ Demonstrates data minimization for compliance
✅ Reduces liability if logs are breached

### What This Does NOT Protect

❌ Sophisticated attackers with rainbow tables
❌ Brute force attacks on common prompts
❌ Determined adversaries with resources

### Real Security Comes From

✅ HTTPS/TLS encryption in transit
✅ API key authentication
✅ Access controls on logs
✅ Secure log storage
✅ Regular key rotation
✅ Monitoring for unauthorized access

---

## Recommendations

### For This System (Current)

✅ **Keep the hash approach** because:

- Prevents casual data leakage
- Demonstrates data minimization
- Helps with compliance
- Low implementation cost
- Good balance of privacy and functionality

### For Production Deployment

⚠️ **Consider these additional measures:**

1. **Don't Store Raw Text Anywhere**
   - API responses: Use hashes ✅ (already done)
   - API logs: Use hashes ✅ (already done)
   - Client side: Keep original text locally, not in shared logs

2. **Encrypt Logs at Rest**
   - Use encryption for log storage
   - Restrict access to encrypted logs
   - Audit log access

3. **Use HTTPS/TLS**
   - All API calls must use HTTPS
   - Enforce TLS 1.2+
   - Use strong certificates

4. **Implement Access Controls**
   - Restrict who can access API
   - Restrict who can read logs
   - Use API key rotation (90-day cycle)

5. **Monitor for Abuse**
   - Alert on unusual access patterns
   - Track failed authentication attempts
   - Monitor for brute force attacks

---

## Summary

### The Hash Change

- **What it does:** Prevents accidental exposure of raw text in responses/logs
- **What it doesn't do:** Provide cryptographic security against sophisticated attacks
- **Real benefit:** Data minimization for compliance and reduced liability

### Real Security Comes From

- HTTPS/TLS encryption in transit
- API key authentication and rotation
- Access controls on logs
- Secure log storage
- Monitoring and alerting

### Best Practice

- Don't return text in API responses (use hashes)
- Don't store raw text in logs (use hashes)
- Keep original text on client side
- Encrypt logs at rest
- Use HTTPS for all communication
- Implement proper access controls

---

## References

- **GDPR Article 5:** Data minimization principle
- **OWASP:** Sensitive Data Exposure
- **NIST:** Cryptographic Standards
- **CWE-532:** Insertion of Sensitive Information into Log File

---

**Key Takeaway:** The hash change is a **data minimization and compliance measure**, not a cryptographic security mechanism. Real security comes from proper access controls, encryption in transit, and operational security practices.
