# Operational Playbook

## Health Monitoring

### Health Check

```bash
curl http://localhost:8000/health
```

Returns `status`, `model_loaded`, `service_degraded`, `circuit_breaker` state, and `model_version`. If the model isn't loaded or the circuit breaker is open, you'll get a 503.

### Metrics

```bash
curl http://localhost:8000/metrics
```

Key Prometheus metrics:

| Metric                          | What it tells you                                       |
| ------------------------------- | ------------------------------------------------------- |
| `http_requests_total`           | Request volume by method, endpoint, status code         |
| `http_request_duration_seconds` | Latency distribution (histogram)                        |
| `prediction_total`              | Prediction count by label (BENIGN/MALICIOUS)            |
| `prediction_errors_total`       | Inference failures — spikes here mean something's wrong |

## Common Operations

### API Key Rotation (Zero-Downtime)

1. Add the new key alongside the old one: `API_KEYS='["old-key","new-key"]'`
2. Restart or redeploy the service
3. Migrate all clients to the new key
4. Remove the old key: `API_KEYS='["new-key"]'`
5. Restart or redeploy again

No requests are rejected during this process as long as both keys are active while clients switch over.

### Circuit Breaker Recovery

The circuit breaker opens when inference fails repeatedly (default: 5 consecutive failures). When it's open, `/health` reports it and predictions return 503.

1. Check logs for the root cause — usually model file corruption or resource exhaustion
2. Verify model files are intact (`ls -lh models/`)
3. The breaker auto-recovers after cooldown (default: 30s)
4. If it keeps tripping, restart the service and investigate the underlying issue

### Log Analysis

All logs are JSON-structured with correlation IDs. Filter by event type:

```bash
# Auth failures (brute-force attempts, bad keys)
docker compose logs backend | grep "auth_failure"

# Prediction errors (model issues, timeouts)
docker compose logs backend | grep "batch_inference_error\|request_error"

# Rate limiting events
docker compose logs backend | grep "rate_limit_exceeded"
```

For production, pipe these into your SIEM or log aggregator (ELK, Splunk, CloudWatch Logs) and set up alerts on the patterns above.

### Model Rollback

If a new model version causes problems:

1. Stop the service
2. Replace model files in `models/` with the previous version
3. Update `MODEL_VERSION` in your `.env` if you track it there
4. Restart — SHA256 checksums are re-verified on startup
5. Confirm via `/health` and `/model-info` that the old version is loaded

## Alerting Thresholds

| Metric                   | Warning   | Critical    |
| ------------------------ | --------- | ----------- |
| Error rate (5min window) | > 1%      | > 5%        |
| p95 latency              | > 200ms   | > 500ms     |
| Circuit breaker state    | half-open | open > 2min |
| Auth failures/min        | > 10      | > 50        |

Set these up in your monitoring stack (Grafana, CloudWatch Alarms, PagerDuty, etc.). The `/metrics` endpoint gives you everything you need for Prometheus-based alerting.
