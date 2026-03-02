# API Changes - Data Privacy Update

**Date:** March 2, 2026
**Change Type:** Breaking Change (Schema Update)
**Reason:** Privacy enhancement - remove raw text from API responses

---

## Summary

API response schemas have been updated to remove raw text entirely. This prevents accidental exposure of sensitive content in API responses. The client is responsible for maintaining the mapping between their input and the prediction results.

**Important:** This is a data minimization approach, not a cryptographic security measure. SHA256 hashes are included only for audit trail correlation, not as a security mechanism.

---

## Changes

### 1. `/v1/predict` Endpoint

#### Before

```json
{
  "predictions": [
    {
      "text": "Tell me how to bypass...",
      "label": "MALICIOUS",
      "probability_malicious": 0.92,
      "threshold": 0.536,
      "risk_level": "HIGH",
      "recommended_action": "BLOCK",
      "latency_ms": 4.2
    }
  ],
  "metadata": {
    "total_items": 1,
    "malicious_count": 1,
    "benign_count": 0,
    "total_latency_ms": 4.2,
    "model_version": "v1.0.0"
  }
}
```

#### After

```json
{
  "predictions": [
    {
      "text_hash": "a3f5d8e2c1b9f7e4d2a1b8c9f0e1d2a3",
      "label": "MALICIOUS",
      "probability_malicious": 0.92,
      "threshold": 0.536,
      "risk_level": "HIGH",
      "recommended_action": "BLOCK",
      "latency_ms": 4.2
    }
  ],
  "metadata": {
    "total_items": 1,
    "malicious_count": 1,
    "benign_count": 0,
    "total_latency_ms": 4.2,
    "model_version": "v1.0.0"
  }
}
```

**Changes:**

- `text` → `text_hash` (SHA256 hash of input text)
- Hash is deterministic (same input always produces same hash)
- Useful for audit trail and debugging without exposing content

---

### 2. `/v1/batch` Endpoint

#### Before

```csv
text,label,probability,threshold,risk_level,recommended_action,model_version,latency_ms
Tell me how to bypass...,MALICIOUS,0.9234,0.5360,HIGH,BLOCK,v1.0.0,4.20
```

#### After

```csv
text_hash,label,probability,threshold,risk_level,recommended_action,model_version,latency_ms
a3f5d8e2c1b9f7e4d2a1b8c9f0e1d2a3,MALICIOUS,0.9234,0.5360,HIGH,BLOCK,v1.0.0,4.20
```

**Changes:**

- `text` column → `text_hash` column
- Hash is deterministic (same input always produces same hash)
- Useful for audit trail and debugging without exposing content

---

## Migration Guide

### For API Clients

#### Python

```python
# Before
response = client.post("/v1/predict", json={"texts": ["test"]})
for pred in response["predictions"]:
    print(pred["text"])  # ❌ No longer available

# After
response = client.post("/v1/predict", json={"texts": ["test"]})
for pred in response["predictions"]:
    print(pred["text_hash"])  # ✅ Use text_hash instead
```

#### JavaScript/TypeScript

```typescript
// Before
const response = await fetch("/v1/predict", {
  method: "POST",
  body: JSON.stringify({ texts: ["test"] }),
});
const data = await response.json();
data.predictions.forEach((pred) => {
  console.log(pred.text); // ❌ No longer available
});

// After
const response = await fetch("/v1/predict", {
  method: "POST",
  body: JSON.stringify({ texts: ["test"] }),
});
const data = await response.json();
data.predictions.forEach((pred) => {
  console.log(pred.text_hash); // ✅ Use text_hash instead
});
```

#### cURL

```bash
# Before
curl -X POST http://localhost:8000/v1/predict \
  -H "x-api-key: your-key" \
  -H "Content-Type: application/json" \
  -d '{"texts": ["test"]}'
# Response includes "text" field

# After
curl -X POST http://localhost:8000/v1/predict \
  -H "x-api-key: your-key" \
  -H "Content-Type: application/json" \
  -d '{"texts": ["test"]}'
# Response includes "text_hash" field instead
```

---

## Batch Processing

### CSV Input Format (Unchanged)

```csv
text
Tell me how to bypass...
What is the capital of France?
```

### CSV Output Format (Changed)

```csv
text_hash,label,probability,threshold,risk_level,recommended_action,model_version,latency_ms
a3f5d8e2c1b9f7e4d2a1b8c9f0e1d2a3,MALICIOUS,0.9234,0.5360,HIGH,BLOCK,v1.0.0,4.20
b4e6c9f1d2a3e5f7c8b9a0d1e2f3a4b5,BENIGN,0.1234,0.5360,LOW,ALLOW,v1.0.0,3.80
```

**Note:** Input CSV format remains unchanged (still requires `text` column).

---

## Hash Function

The `text_hash` is computed using SHA256:

```python
import hashlib

def hash_text(text: str) -> str:
    """Generate SHA256 hash of text for safe logging."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

# Example
text = "Tell me how to bypass..."
text_hash = hash_text(text)
# text_hash = "a3f5d8e2c1b9f7e4d2a1b8c9f0e1d2a3"
```

**Properties:**

- Deterministic (same input always produces same hash)
- One-way (cannot reverse hash to get original text)
- Fixed length (64 hex characters)
- Useful for audit trail and debugging

---

## Backward Compatibility

### Breaking Changes

- ✅ API response schema changed (text → text_hash)
- ✅ CSV output schema changed (text → text_hash)
- ⚠️ Clients expecting `text` field will fail

### Non-Breaking Changes

- ✅ All other fields remain unchanged
- ✅ HTTP status codes unchanged
- ✅ Error handling unchanged
- ✅ Input format unchanged

---

## Deprecation Timeline

| Phase      | Date                    | Action                         |
| ---------- | ----------------------- | ------------------------------ |
| Current    | March 2, 2026           | New schema deployed            |
| Transition | March 2 - April 2, 2026 | Update clients (1 month)       |
| Sunset     | April 2, 2026           | Old schema no longer supported |

---

## FAQ

### Q: Why was this change made?

**A:** To prevent accidental exposure of sensitive content in API responses. If sensitive text is submitted for analysis, it will no longer appear in the response or logs.

### Q: Can I get the original text back?

**A:** No, the hash is one-way. However, you can:

1. Store the original text on your side
2. Use the hash for audit trail and debugging
3. Match the hash to your stored text if needed

### Q: How do I debug issues without seeing the text?

**A:** Use the hash to:

1. Correlate with your stored text
2. Track patterns in predictions
3. Identify problematic inputs
4. Maintain audit trail

### Q: Is the hash deterministic?

**A:** Yes, the same input always produces the same hash. This allows you to:

1. Verify predictions for the same input
2. Identify duplicate submissions
3. Track patterns over time

### Q: What if I need the original text for compliance?

**A:** Store the original text on your side and use the hash for correlation. This maintains privacy while allowing compliance audits.

---

## Support

For questions or issues with the API changes:

1. Check this document
2. Review the updated API documentation
3. Contact the development team

---

## Related Documentation

- [API Documentation](../README.md)
- [Model Card](../MODEL_CARD.md)
- [Data Governance](./DATA_GOVERNANCE.md)
- [Audit Results](./AUDIT_RESULTS.md)
