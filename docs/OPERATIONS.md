# Operational Playbook

## Health Monitoring

### Health Check

```bash
curl http://localhost:8000/health
```

Expected response includes: `status`, `model_loaded`, `service_degraded`, `circuit_breaker`, `model_version`.

### Metrics

```bash
curl http://localhost:8000/metrics
```

Key metrics to monitor:

- `http_requests_total` — request volume by status code
- `http_request_duration_seconds` — latency percentiles
- `prediction_total` — predictions by label (BENIGN/MALICIOUS)
- `prediction_errors_total` — inference failures

## Common Operations

### API Key Rotation (Zero-Downtime)

1. Add new key to `API_KEYS` environment variable: `API_KEYS='["old-key","new-key"]'`
2. Restart/redeploy the service
3. Update all clients to use the new key
4. Remove old key: `API_KEYS='["new-key"]'`
5. Restart/redeploy

### Circuit Breaker Recovery

If the circuit breaker opens (visible in `/health` response):

1. Check logs for inference errors
2. Verify model files are intact
3. The breaker auto-recovers after cooldown (default: 30s)
4. If persistent, restart the service

### Log Analysis

Logs are JSON-structured. Filter by event type:

```bash
# Auth failures
docker compose logs backend | grep "auth_failure"

# Prediction errors
docker compose logs backend | grep "batch_inference_error\|request_error"

# Rate limiting
docker compose logs backend | grep "rate_limit_exceeded"
```

## Alerting Thresholds

| Metric            | Warning   | Critical    |
| ----------------- | --------- | ----------- |
| Error rate (5min) | > 1%      | > 5%        |
| p95 latency       | > 200ms   | > 500ms     |
| Circuit breaker   | half-open | open > 2min |
| Auth failures/min | > 10      | > 50        |
