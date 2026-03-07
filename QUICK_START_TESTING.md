# Quick Start: Testing & Load Testing

Fast reference for running tests and load tests.

---

## Setup

```bash
# Install dependencies
pip install -r requirements-dev.txt
cd frontend && npm install && cd ..

# Start services
docker compose up --build

# Or run locally
uvicorn api.app:app --reload  # Terminal 1
cd frontend && npm run dev     # Terminal 2
```

---

## Run Tests

### All Tests
```bash
pytest tests/ -v
```

### Fast Tests Only (Pre-commit)
```bash
pytest tests/ -m "not slow and not integration" -v
```

### Specific Test File
```bash
pytest tests/test_e2e.py -v
pytest tests/test_api.py -v
pytest tests/test_basic.py -v
```

### With Coverage
```bash
pytest tests/ --cov=src --cov=api --cov-report=html
open htmlcov/index.html
```

---

## Run E2E Tests

### All E2E Tests
```bash
pytest tests/test_e2e.py -v
```

### Specific E2E Test Class
```bash
pytest tests/test_e2e.py::TestE2EAnalyzeWorkflow -v
pytest tests/test_e2e.py::TestE2EBatchWorkflow -v
pytest tests/test_e2e.py::TestE2ESecurityWorkflow -v
```

### Specific E2E Test
```bash
pytest tests/test_e2e.py::TestE2EAnalyzeWorkflow::test_single_prediction_workflow -v
```

---

## Run Load Tests

### All Load Tests
```bash
python tests/load_test.py
```

### Single Prediction Load Test Only
```bash
python -c "from tests.load_test import single_prediction_load_test; single_prediction_load_test()"
```

### Batch Prediction Load Test Only
```bash
python -c "from tests.load_test import batch_prediction_load_test; batch_prediction_load_test()"
```

### Sustained Load Test (60 seconds)
```bash
python -c "from tests.load_test import sustained_load_test; sustained_load_test(60)"
```

### Sustained Load Test (120 seconds)
```bash
python -c "from tests.load_test import sustained_load_test; sustained_load_test(120)"
```

---

## Performance Benchmarks

### Run Performance Benchmarks
```bash
pytest tests/perf_check.py -v
```

### Expected Results
- Single prediction: ~4ms p50
- Batch (10 items): ~20ms p50
- Throughput: ~250 req/sec

---

## Load Test Configuration

Edit `tests/load_test.py` to adjust:

```python
SINGLE_PREDICTION_LOAD = 100      # Number of single predictions
BATCH_SIZE = 50                   # Items per batch
BATCH_LOAD = 10                   # Number of batches
CONCURRENT_WORKERS = 10           # Concurrent requests

# Thresholds
LATENCY_P50_THRESHOLD = 10        # ms
LATENCY_P95_THRESHOLD = 50        # ms
LATENCY_P99_THRESHOLD = 200       # ms
ERROR_RATE_THRESHOLD = 0.01       # 1%
```

---

## Continuous Testing

### Watch Mode (Auto-run on file changes)
```bash
pytest-watch tests/ -- -v
```

### Run Tests on Commit
```bash
./scripts/setup-hooks.sh  # Install pre-commit hooks
git commit -m "Your message"  # Hooks run automatically
```

---

## Debugging Tests

### Run with Print Statements
```bash
pytest tests/test_e2e.py -v -s
```

### Run with Debugger
```bash
pytest tests/test_e2e.py -v --pdb
```

### Run Specific Test with Verbose Output
```bash
pytest tests/test_e2e.py::TestE2EAnalyzeWorkflow::test_single_prediction_workflow -vv -s
```

---

## Integration with CI/CD

### GitHub Actions
Tests run automatically on:
- Every push to main/develop
- Every pull request

### Local Pre-commit
```bash
# Install hooks
./scripts/setup-hooks.sh

# Hooks run automatically on commit
git commit -m "Your message"

# Skip hooks (emergency only)
git commit --no-verify -m "Emergency fix"
```

### Ship with Full Validation
```bash
./ship.sh "Your commit message"
```

---

## Troubleshooting

### Tests Fail with "Connection refused"
```bash
# Make sure API is running
curl http://localhost:8000/health

# If not running, start it
docker compose up backend
# or
uvicorn api.app:app --reload
```

### Load Tests Show High Error Rate
```bash
# Check API health
curl http://localhost:8000/health

# Check logs
docker logs backend

# Reduce concurrent workers
# Edit CONCURRENT_WORKERS in tests/load_test.py
```

### E2E Tests Timeout
```bash
# Increase timeout in test
# Edit timeout parameter in requests.post()

# Or check if API is slow
python tests/perf_check.py
```

---

## Test Organization

```
tests/
├── test_api.py              # API integration tests
├── test_basic.py            # Basic functionality
├── test_circuit_breaker.py  # Circuit breaker tests
├── test_rate_limiter.py     # Rate limiting tests
├── test_error_handling.py   # Error handling
├── test_hmac.py             # HMAC signature tests
├── test_mocked_predict.py   # Mocked predictions
├── test_ai_audit.py         # AI behavior audit
├── test_logic_audit.py      # Logic audit
├── test_adversarial.py      # Adversarial inputs
├── test_cache.py            # Cache behavior
├── test_dependencies.py     # Dependency injection
├── test_input_validation.py # Input validation
├── test_normalization_parity.py  # Train/serve parity
├── test_fallback.py         # Fallback predictor
├── test_e2e.py              # End-to-end workflows (NEW)
├── load_test.py             # Load testing (NEW)
├── perf_check.py            # Performance benchmarks
└── conftest.py              # Shared fixtures
```

---

## Quick Commands

```bash
# Run all tests
pytest tests/ -v

# Run fast tests only
pytest tests/ -m "not slow and not integration" -v

# Run E2E tests
pytest tests/test_e2e.py -v

# Run load tests
python tests/load_test.py

# Run with coverage
pytest tests/ --cov=src --cov=api

# Run specific test
pytest tests/test_e2e.py::TestE2EAnalyzeWorkflow::test_single_prediction_workflow -v

# Run with debugging
pytest tests/test_e2e.py -v -s --pdb

# Watch mode
pytest-watch tests/ -- -v

# Ship with full validation
./ship.sh "Your commit message"
```

---

## Performance Targets

| Metric | Target | Warning | Critical |
| --- | --- | --- | --- |
| p50 latency | <10ms | >10ms | >50ms |
| p95 latency | <50ms | >50ms | >200ms |
| p99 latency | <200ms | >200ms | >500ms |
| Error rate | <0.1% | >1% | >5% |
| Throughput | >100 req/s | <100 req/s | <50 req/s |
| Cache hit rate | >70% | <70% | <20% |

---

## Next Steps

1. **Run E2E tests** - Verify full workflows work
2. **Run load tests** - Check performance under load
3. **Review results** - Compare against thresholds
4. **Optimize if needed** - Adjust cache size, workers, etc.
5. **Document findings** - Update SCALING_STRATEGY.md

See `docs/SHOWCASE_GUIDE.md` for interview preparation.
