"""Shared FastAPI dependencies for route handlers."""

import json
import logging
from typing import Optional, cast

from fastapi import HTTPException, Request

from src.config import settings
from src.inference.base import BasePredictor
from src.utils.circuit_breaker import CircuitBreaker
from src.utils.metrics import Metrics
from src.utils.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)


def require_api_key(request: Request) -> None:
    """Validate API key from request headers with rate-limited auth failure tracking."""
    if not settings.api_keys:
        logger.error("API Keys not configured in settings")
        raise HTTPException(
            status_code=500, detail="Server configuration error: No API keys configured"
        )

    client_ip = request.client.host if request.client else "unknown"
    try:
        auth_limiter: RateLimiter = request.app.state.auth_rate_limiter
    except AttributeError:
        logger.warning("Auth rate limiter not initialized")
        auth_limiter = RateLimiter(
            settings.auth_rate_limit_max, settings.auth_rate_limit_window
        )

    if auth_limiter.is_blocked(client_ip):
        logger.warning(
            json.dumps(
                {
                    "event": "auth_rate_limit_exceeded",
                    "client_ip": client_ip,
                    "correlation_id": getattr(request.state, "correlation_id", None),
                }
            )
        )
        raise HTTPException(
            status_code=429,
            detail="Too many authentication attempts",
            headers={"Retry-After": "60"},
        )

    provided = request.headers.get("x-api-key", "")
    if provided not in settings.api_keys:
        auth_limiter.record_attempt(client_ip)
        logger.warning(
            json.dumps(
                {
                    "event": "invalid_api_key",
                    "client_ip": client_ip,
                    "correlation_id": getattr(request.state, "correlation_id", None),
                }
            )
        )
        raise HTTPException(status_code=403, detail="Invalid API key")


def resolve_threshold(predictor: Optional[BasePredictor] = None) -> float:
    """Resolve the effective decision threshold from settings or model config."""
    if settings.decision_threshold is not None:
        return float(settings.decision_threshold)
    if predictor is not None:
        return float(predictor.config["optimal_threshold"])
    raise HTTPException(status_code=500, detail="No decision threshold configured")


def get_predictor(request: Request) -> BasePredictor:
    """Get predictor from app state with validation."""
    predictor: Optional[BasePredictor] = getattr(request.app.state, "predictor", None)
    if predictor is None:
        raise HTTPException(status_code=503, detail="Model unavailable")
    return predictor


def get_metrics(request: Request) -> Metrics:
    """Get metrics instance from app state."""
    metrics: Optional[Metrics] = getattr(request.app.state, "metrics", None)
    if metrics is None:
        # Fallback: create temporary metrics instance
        logger.warning("Metrics not initialized, using temporary instance")
        return Metrics()
    return metrics


def get_circuit_breaker(request: Request) -> Optional[CircuitBreaker]:
    """Get circuit breaker from app state (may be None if disabled)."""
    breaker = getattr(request.app.state, "breaker", None)
    # Allow mocks in tests (they have the necessary methods)
    if breaker is None:
        return None
    # In production, verify it's the right type; in tests, trust the mock
    if not isinstance(breaker, CircuitBreaker) and not hasattr(breaker, "_mock_name"):
        return None
    return cast(CircuitBreaker, breaker)


def get_rate_limiter(request: Request) -> RateLimiter:
    """Get rate limiter from app state."""
    limiter: Optional[RateLimiter] = getattr(request.app.state, "rate_limiter", None)
    if limiter is None:
        # Fallback: create temporary rate limiter
        logger.warning("Rate limiter not initialized, using temporary instance")
        return RateLimiter(settings.rate_limit_max, settings.rate_limit_window)
    return limiter


def check_rate_limit(request: Request) -> None:
    """Check rate limit for client IP and raise exception if exceeded."""
    if not request.client or not request.client.host:
        raise HTTPException(status_code=400, detail="Could not determine client IP")

    client_ip = request.client.host
    rate_limiter = get_rate_limiter(request)

    if not rate_limiter.is_allowed(client_ip):
        logger.warning(
            json.dumps(
                {
                    "event": "rate_limit_exceeded",
                    "correlation_id": getattr(request.state, "correlation_id", None),
                    "client_ip": client_ip,
                }
            )
        )
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded",
            headers={"Retry-After": str(settings.rate_limit_window)},
        )


def check_circuit_breaker(request: Request) -> None:
    """Check circuit breaker status and raise exception if open."""
    breaker = get_circuit_breaker(request)
    if breaker and not breaker.allow_request():
        metrics = get_metrics(request)
        metrics.record_error()
        raise HTTPException(status_code=503, detail="Inference temporarily unavailable")
