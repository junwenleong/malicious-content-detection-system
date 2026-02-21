import json
import logging
import time
import uuid
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Dict, List, cast

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from src.api.middleware import AuditMiddleware, SecurityHeadersMiddleware, PrometheusMiddleware
from src.config import settings
from src.inference.predictor import Predictor
from src.utils.circuit_breaker import CircuitBreaker
from src.utils.metrics import Metrics
from src.utils.rate_limiter import RateLimiter

# Import routers
from src.api.routes import health, predict, batch, metrics

logging.basicConfig(
    level=logging.INFO,
    format='{"time":"%(asctime)s","name":"%(name)s","level":"%(levelname)s","message":"%(message)s"}',
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    try:
        app.state.predictor = Predictor(settings.model_path, settings.config_path)
    except Exception:
        app.state.predictor = None
    app.state.metrics = Metrics()
    app.state.rate_limiter = RateLimiter(
        settings.rate_limit_max, settings.rate_limit_window
    )
    # Strict rate limiter for authentication failures (5 attempts per minute)
    app.state.auth_rate_limiter = RateLimiter(5, 60)
    app.state.breaker = (
        CircuitBreaker(
            settings.breaker_failure_threshold,
            settings.breaker_cooldown_seconds,
        )
        if settings.breaker_enabled
        else None
    )
    logger.info("Application startup complete")
    yield
    logger.info("Application shutdown initiated")
    # Clean up resources if needed (e.g. close DB connections)


app = FastAPI(
    title="Malicious Content Detection API",
    version="3.0",
    description=(
        "ML-based malicious content detection for agency's LLM. "
        "Provides real-time predictions and batch processing for abuse detection in text-based APIs. "
        "Model: TF-IDF + Calibrated Logistic Regression."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(SecurityHeadersMiddleware)
if settings.audit_log_enabled:
    app.add_middleware(AuditMiddleware)

app.add_middleware(PrometheusMiddleware)


@app.middleware("http")
async def log_requests(request: Request, call_next: Any) -> Response:
    correlation_id = (
        request.headers.get("x-correlation-id")
        or request.headers.get("x-request-id")
        or str(uuid.uuid4())
    )
    request.state.correlation_id = correlation_id
    start_time = time.time()
    try:
        response = await call_next(request)
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(
            json.dumps(
                {
                    "event": "request_error",
                    "correlation_id": correlation_id,
                    "method": request.method,
                    "path": request.url.path,
                    "error": str(e)[:500],
                    "duration_ms": round(process_time * 1000, 2),
                }
            )
        )
        # RFC 7807 Problem Details for 500s
        error_response = Response(
            content=json.dumps(
                {
                    "type": "about:blank",
                    "title": "Internal Server Error",
                    "status": 500,
                    "detail": "An unexpected error occurred while processing the request.",
                    "instance": request.url.path,
                    "correlation_id": correlation_id,
                }
            ),
            status_code=500,
            media_type="application/problem+json",
        )
        error_response.headers["x-correlation-id"] = correlation_id
        return error_response
    process_time = time.time() - start_time
    response.headers["x-correlation-id"] = correlation_id
    logger.info(
        json.dumps(
            {
                "event": "request_completed",
                "correlation_id": correlation_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(process_time * 1000, 2),
            }
        )
    )
    return cast(Response, response)


# Include Routers
app.include_router(health.router)
app.include_router(predict.router)
app.include_router(batch.router)
app.include_router(metrics.router)


@app.get("/")
def root() -> Dict[str, Any]:
    return {
        "message": "Malicious Content Detection API - Production Grade",
        "version": "3.0",
        "endpoints": {
            "predict": "/v1/predict",
            "batch": "/v1/batch",
            "health": "/health",
            "metrics": "/metrics",
            "model_info": "/model-info",
            "docs": "/docs",
        },
    }


