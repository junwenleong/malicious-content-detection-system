---
inclusion: always
---

# Anti-Patterns — What Not To Do

Specific mistakes that have occurred or are likely in this codebase. These are hard rules, not suggestions.

## Python Backend — Malicious Content Detection System

**Never modify the predictor interface without updating all routes.** The predictor is the core inference layer. Changes to `predict()` or `apredict()` signatures cascade to `/v1/predict`, `/v1/batch`, and fallback logic. Always update all three simultaneously.

**Never hardcode policy thresholds in route handlers.** Risk level boundaries (0.85, 0.6) and action margins (0.15) are now centralized in `src/utils/policy.py`. Changes must go there, not scattered across routes. This prevents inconsistency between endpoints.

**Never add new environment variables without validation in `src/config.py`.** Config changes must be validated at startup with proper type hints and bounds checking. Missing vars should fail-fast with clear error messages, not silently default.

**Never bypass the text normalization utility.** Always use `src.utils.text.normalize_text()` for both training and inference. Direct normalization in routes or predictor methods causes train/serve skew and evasion vulnerabilities.

**Never log raw text or user input.** Use `src.utils.text.hash_text()` for safe logging. Raw text in logs exposes sensitive content in heap dumps and violates privacy. Hash it or omit it.

**Never modify rate limiter or circuit breaker logic without thread safety review.** These utilities use locks for concurrent access. Changes must maintain thread safety or risk race conditions under load.

**Never add new API endpoints without security headers middleware.** All responses must include HSTS, CSP, X-Frame-Options, etc. These are applied globally via `SecurityHeadersMiddleware`, not per-route.

## TypeScript Frontend — React + MUI

**Never add new components without error boundary wrapping.** Component crashes should not crash the entire app. Use the `ErrorBoundary` component to isolate failures.

**Never hardcode API URLs in components.** Always use the `apiUrl` prop passed from `App.tsx`. Hardcoding breaks deployments to different environments.

**Never assume synchronous API responses.** Always handle loading and error states. Use `useState` for loading flags and error messages. Never block UI while waiting for API calls.

**Never use `any` types in TypeScript.** All props and state must have explicit types. Use `interface` for component props and `type` for unions. This catches bugs at compile time.

**Never modify theme colors directly in components.** All colors come from `theme.ts`. Component-level color overrides break consistency and make theme changes impossible.

## Architecture — Layering & Coupling

**Never call inference directly from routes.** Always go through dependency injection (`get_predictor()`, `get_metrics()`, etc.). This enables testing with mocks and swapping implementations.

**Never add business logic to route handlers.** Policy decisions, risk level calculation, and action determination belong in `src/utils/policy.py`. Routes should orchestrate, not decide.

**Never store state in app globals.** Use `request.app.state` for request-scoped dependencies (predictor, metrics, circuit breaker). This enables testing and prevents state leaks between requests.

**Never skip the circuit breaker for inference calls.** Always check `check_circuit_breaker()` dependency before calling the predictor. This prevents cascading failures when the model is unhealthy.

## Testing — Coverage & Markers

**Never write slow tests without the `@pytest.mark.slow` marker.** Unmarked tests run in pre-commit and block commits. Mark integration tests, performance tests, and anything >100ms as slow.

**Never mock the predictor without using `FallbackPredictor`.** Tests should use the real predictor or the fallback. Mocking with arbitrary return values hides real inference bugs.

**Never test without correlation IDs.** All audit logs and metrics should include correlation IDs for traceability. Tests should verify this is present in logs.

## Security — Input & Output

**Never trust user input without normalization.** Always call `normalize_text()` on input before inference. This prevents homoglyph evasion and control character injection.

**Never output raw predictions without sanitization.** CSV batch output must sanitize cells with `_sanitize_csv_cell()` to prevent formula injection in spreadsheet applications.

**Never expose stack traces to clients.** All exceptions must be caught and converted to RFC 7807 Problem Details responses. Stack traces are logged internally, never returned to clients.

**Never allow unbounded file uploads.** Batch endpoint enforces `max_csv_bytes` (10MB default). Always validate file size before processing.

## Configuration — Secrets & Defaults

**Never commit `.env` files.** Only commit `.env.*.example` files with placeholder values. Real secrets go in environment variables or secrets management systems.

**Never use weak API keys.** Keys should be at least 32 characters. The config validator enforces this for HMAC secrets; apply the same standard to API keys.

**Never disable security features in production.** HMAC signing, rate limiting, and circuit breaker should be enabled. Disabling them for "convenience" creates vulnerabilities.

**Never hardcode model paths or checksums.** These come from config. Hardcoding breaks deployments and prevents model updates without code changes.

## Performance — Caching & Optimization

**Never bypass the LRU cache.** Always call `predictor.predict()` which checks cache first. Direct model calls skip caching and hurt performance.

**Never increase cache size without memory analysis.** The 10k item cache is tuned for typical deployments. Larger caches consume more memory; smaller caches reduce hit rates. Measure before changing.

**Never process batch items sequentially.** Batch processing uses `joblib` for parallelization. Never add sequential loops that defeat this optimization.

**Never add synchronous I/O in async routes.** Use `asyncio.to_thread()` for blocking operations. Synchronous I/O blocks the event loop and hurts throughput.

## Observability — Logging & Metrics

**Never log without correlation IDs.** Every log entry should include the correlation ID from `request.state.correlation_id`. This enables end-to-end tracing.

**Never use string formatting for logs.** Always use JSON structured logging with `json.dumps()`. This enables log aggregation and querying.

**Never add unbounded metric labels.** Prometheus metrics use `_normalize_path()` to bucket unknown paths as "other". This prevents cardinality explosion. Follow this pattern for all new metrics.

**Never expose internal error details in metrics.** Metrics should track counts and latencies, not error messages. Error details go in logs, not metrics.
