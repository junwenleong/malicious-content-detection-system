# Operational Runbook

Troubleshooting guide for common issues and operational tasks.

---

## Health Checks

### Quick Health Check

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "model_version": "v1.0.0",
  "model_available": true,
  "cache_stats": {
    "cache_size": 1234,
    "cache_max_size": 10000,
    "hit_rate": 0.75
  }
}
```

### Detailed Model Info

```bash
curl -H "x-api-key: your-key" http://localhost:8000/model-info
```

---

## Common Issues & Solutions

### Issue 1: "Model unavailable" Error

**Symptoms:**
- API returns 503 Service Unavailable
- Health endpoint shows `model_available: false`

**Diagnosis:**
```bash
# Check if model files exist
ls -la models/malicious_content_detector_*.pkl

# Check model checksums
sha256sum models/malicious_content_detector_calibrated.pkl
sha256sum models/malicious_content_detector_config.pkl
```

**Solutions:**

1. **Model files missing** - Train the model:
   ```bash
   python scripts/train_model.py
   ```

2. **Checksum mismatch** - Model was corrupted or replaced:
   ```bash
   # Update checksums in .env
   python scripts/update_checksums.sh
   ```

3. **Permission issues** - Check file permissions:
   ```bash
   chmod 644 models/*.pkl
   ```

4. **Restart service** - Restart the API:
   ```bash
   docker compose restart backend
   # or
   pkill -f "gunicorn.*api.app"
   ```

---

### Issue 2: Rate Limiting (429 Errors)

**Symptoms:**
- API returns 429 Too Many Requests
- Response includes `Retry-After` header

**Diagnosis:**
```bash
# Check current rate limit settings
grep RATE_LIMIT .env

# Check metrics for request patterns
curl -H "x-api-key: your-key" http://localhost:8000/metrics | grep http_requests_total
```

**Solutions:**

1. **Legitimate high traffic** - Increase rate limit:
   ```bash
   # In .env
   RATE_LIMIT_MAX=200  # Increase from 100
   RATE_LIMIT_WINDOW=60
   ```

2. **Brute-force attack** - Check logs:
   ```bash
   docker logs backend | grep "rate_limit_exceeded"
   ```

3. **Client implementation issue** - Implement exponential backoff:
   ```python
   import time
   for attempt in range(3):
       response = requests.post(...)
       if response.status_code == 429:
           wait_time = int(response.headers.get("Retry-After", 60))
           time.sleep(wait_time)
           continue
       break
   ```

---

### Issue 3: Slow Predictions (High Latency)

**Symptoms:**
- Predictions take >100ms
- Health check shows low cache hit rate

**Diagnosis:**
```bash
# Check cache statistics
curl -H "x-api-key: your-key" http://localhost:8000/model-info | jq .cache_stats

# Check metrics for latency
curl -H "x-api-key: your-key" http://localhost:8000/metrics | grep http_request_duration_seconds
```

**Solutions:**

1. **Low cache hit rate** - Increase cache size:
   ```bash
   # In .env
   PREDICTION_CACHE_SIZE=20000  # Increase from 10000
   ```

2. **Insufficient workers** - Check worker count:
   ```bash
   # In docker-compose.yml or entrypoint.sh
   WORKERS=8  # Increase based on CPU cores
   ```

3. **Model too large** - Check model file size:
   ```bash
   ls -lh models/malicious_content_detector_calibrated.pkl
   ```

4. **System resource constraints** - Monitor CPU/memory:
   ```bash
   docker stats backend
   ```

---

### Issue 4: Authentication Failures (403 Errors)

**Symptoms:**
- API returns 403 Forbidden
- Logs show "invalid_api_key" events

**Diagnosis:**
```bash
# Check configured API keys
grep API_KEY .env

# Check auth logs
docker logs backend | grep "invalid_api_key"
```

**Solutions:**

1. **Wrong API key** - Verify key is correct:
   ```bash
   curl -H "x-api-key: correct-key" http://localhost:8000/health
   ```

2. **Key not configured** - Add API key to .env:
   ```bash
   API_KEYS='["key1", "key2"]'
   ```

3. **Brute-force lockout** - Check auth rate limiter:
   ```bash
   docker logs backend | grep "auth_rate_limit_exceeded"
   # Wait 60 seconds or restart service
   ```

---

### Issue 5: Circuit Breaker Open (503 Errors)

**Symptoms:**
- API returns 503 Service Unavailable
- Logs show "circuit_breaker_open"

**Diagnosis:**
```bash
# Check circuit breaker status
curl -H "x-api-key: your-key" http://localhost:8000/model-info | jq .circuit_breaker

# Check error logs
docker logs backend | grep "circuit_breaker"
```

**Solutions:**

1. **Temporary model failures** - Wait for cooldown:
   ```bash
   # Default cooldown is 30 seconds
   # Check BREAKER_COOLDOWN_SECONDS in .env
   sleep 30
   curl http://localhost:8000/health
   ```

2. **Persistent model failures** - Investigate root cause:
   ```bash
   docker logs backend | grep "Prediction error"
   ```

3. **Disable circuit breaker** (emergency only):
   ```bash
   # In .env
   BREAKER_ENABLED=false
   # Restart service
   docker compose restart backend
   ```

---

### Issue 6: CSV Batch Processing Fails

**Symptoms:**
- Batch endpoint returns 400 Bad Request
- Error message about CSV format

**Diagnosis:**
```bash
# Check CSV file format
head -5 input.csv

# Validate CSV structure
python -c "import csv; csv.DictReader(open('input.csv')).fieldnames"
```

**Solutions:**

1. **Missing 'text' column** - CSV must have a 'text' column:
   ```csv
   text
   "Hello world"
   "Ignore previous instructions"
   ```

2. **Invalid encoding** - Ensure UTF-8 encoding:
   ```bash
   file input.csv
   iconv -f ISO-8859-1 -t UTF-8 input.csv > input_utf8.csv
   ```

3. **File too large** - Check file size:
   ```bash
   ls -lh input.csv
   # Default limit is 10MB
   # Increase MAX_CSV_BYTES in .env if needed
   ```

4. **Invalid MIME type** - Use text/csv:
   ```bash
   curl -F "file=@input.csv;type=text/csv" \
     -H "x-api-key: your-key" \
     http://localhost:8000/v1/batch
   ```

---

## Maintenance Tasks

### API Key Rotation (Zero-Downtime)

```bash
# 1. Add new key to API_KEYS list
API_KEYS='["old-key", "new-key"]'

# 2. Restart service (old key still works)
docker compose restart backend

# 3. Update clients to use new key

# 4. Remove old key from API_KEYS
API_KEYS='["new-key"]'

# 5. Restart service
docker compose restart backend
```

### Model Update

```bash
# 1. Train new model
python scripts/train_model.py

# 2. Update checksums
python scripts/update_checksums.sh

# 3. Update .env with new checksums
# (or let validation fail and copy from error message)

# 4. Restart service
docker compose restart backend

# 5. Verify health
curl http://localhost:8000/health
```

### Cache Clearing

```bash
# Clear prediction cache (useful after model update)
curl -X POST -H "x-api-key: your-key" \
  http://localhost:8000/cache/clear

# Or restart service
docker compose restart backend
```

### Log Analysis

```bash
# View recent errors
docker logs backend | grep "ERROR\|error" | tail -20

# View auth events
docker logs backend | grep "auth_" | tail -20

# View rate limit events
docker logs backend | grep "rate_limit" | tail -20

# View circuit breaker events
docker logs backend | grep "circuit_breaker" | tail -20

# Export logs to file
docker logs backend > backend.log 2>&1
```

---

## Monitoring & Alerting

### Key Metrics to Monitor

1. **Request latency** - p50, p95, p99
   ```bash
   curl -H "x-api-key: your-key" http://localhost:8000/metrics | \
     grep http_request_duration_seconds
   ```

2. **Error rate** - 4xx and 5xx responses
   ```bash
   curl -H "x-api-key: your-key" http://localhost:8000/metrics | \
     grep "http_requests_total.*status=\"5"
   ```

3. **Cache hit rate** - Should be >70% in production
   ```bash
   curl -H "x-api-key: your-key" http://localhost:8000/model-info | \
     jq .cache_stats.hit_rate
   ```

4. **Circuit breaker state** - Should be "closed" in normal operation
   ```bash
   curl -H "x-api-key: your-key" http://localhost:8000/model-info | \
     jq .circuit_breaker.state
   ```

### Alert Thresholds

| Metric | Warning | Critical |
| --- | --- | --- |
| Latency p95 | >50ms | >200ms |
| Error rate | >1% | >5% |
| Cache hit rate | <50% | <20% |
| Circuit breaker | half-open | open |
| Model unavailable | N/A | true |

---

## Disaster Recovery

### Backup Model Files

```bash
# Backup current model
cp models/malicious_content_detector_calibrated.pkl \
   models/backup_$(date +%Y%m%d_%H%M%S)_calibrated.pkl

# Backup config
cp models/malicious_content_detector_config.pkl \
   models/backup_$(date +%Y%m%d_%H%M%S)_config.pkl
```

### Restore from Backup

```bash
# List backups
ls -la models/backup_*

# Restore specific backup
cp models/backup_20260307_120000_calibrated.pkl \
   models/malicious_content_detector_calibrated.pkl

# Update checksums
python scripts/update_checksums.sh

# Restart service
docker compose restart backend
```

### Rollback to Previous Version

```bash
# If using Docker images with tags
docker compose down
docker compose -f docker-compose.prod.yml up -d --image malicious-content-detection:v1.0.0

# Or restart with previous model
git checkout HEAD~1 models/
python scripts/update_checksums.sh
docker compose restart backend
```

---

## Performance Tuning

### Increase Throughput

```bash
# Increase worker count
WORKERS=16  # Based on CPU cores

# Increase batch size
MAX_BATCH_ITEMS=2000  # From 1000

# Increase cache size
PREDICTION_CACHE_SIZE=50000  # From 10000

# Restart service
docker compose restart backend
```

### Reduce Latency

```bash
# Reduce batch size (faster processing)
MAX_BATCH_ITEMS=500

# Increase cache size (more hits)
PREDICTION_CACHE_SIZE=20000

# Reduce timeout
# In entrypoint.sh: --timeout 20 (from 30)

# Restart service
docker compose restart backend
```

---

## Escalation Path

### Level 1: Automated Monitoring
- Health checks every 30 seconds
- Alert on circuit breaker open
- Alert on error rate >5%

### Level 2: On-Call Engineer
- Investigate logs
- Check metrics
- Attempt restart/recovery

### Level 3: Engineering Team
- Root cause analysis
- Model retraining if needed
- Infrastructure changes

### Level 4: Incident Commander
- Declare SEV-1 incident
- Coordinate response
- Post-mortem after resolution

---

## Contact & Escalation

- **On-Call:** [Slack channel or phone]
- **Engineering Lead:** [Contact info]
- **Infrastructure Team:** [Contact info]
- **Incident Commander:** [Contact info]

---

## Additional Resources

- [Threat Model](THREAT_MODEL.md) - Security considerations
- [Scaling Strategy](SCALING_STRATEGY.md) - Performance limits
- [API Reference](API_REFERENCE.md) - Endpoint documentation
- [Deployment Guide](DEPLOYMENT.md) - Infrastructure setup
