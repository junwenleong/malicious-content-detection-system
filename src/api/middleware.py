import logging
import time
import json
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response
from prometheus_client import Counter, Histogram

logger = logging.getLogger("audit")

REQUEST_COUNT = Counter(
    "http_requests_total", "Total HTTP Requests", ["method", "endpoint", "status"]
)
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds", "HTTP Request Duration", ["method", "endpoint"]
)


class PrometheusMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        start_time = time.monotonic()
        status_code = 500

        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception as e:
            # Let exception bubble up, but log 500 first
            status_code = 500
            raise e
        finally:
            duration = time.monotonic() - start_time
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=request.url.path,
                status=str(status_code),
            ).inc()
            REQUEST_LATENCY.labels(
                method=request.method, endpoint=request.url.path
            ).observe(duration)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        response = await call_next(request)
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["X-XSS-Protection"] = "0"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=()"
        )
        return response


class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        client_ip = request.client.host if request.client else "unknown"
        path = request.url.path
        correlation_id = getattr(request.state, "correlation_id", None)

        response = await call_next(request)

        # Log Auth Events
        # 401/403 are definitive failures
        if response.status_code in [401, 403]:
            logger.warning(
                json.dumps(
                    {
                        "event": "auth_failure",
                        "client_ip": client_ip,
                        "path": path,
                        "status_code": response.status_code,
                        "method": request.method,
                        "correlation_id": correlation_id,
                    }
                )
            )
        # Success (2xx) on protected paths (heuristic: has api key header)
        elif response.status_code < 400 and "x-api-key" in request.headers:
            logger.info(
                json.dumps(
                    {
                        "event": "auth_success",
                        "client_ip": client_ip,
                        "path": path,
                        "status_code": response.status_code,
                        "method": request.method,
                        "correlation_id": correlation_id,
                    }
                )
            )

        return response
