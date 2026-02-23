"""Shared FastAPI dependencies for route handlers."""

import json
import logging
from typing import Optional

from fastapi import HTTPException, Request

from src.config import settings
from src.inference.predictor import Predictor
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
        auth_limiter = RateLimiter(5, 60)

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


def resolve_threshold(predictor: Optional[Predictor] = None) -> float:
    """Resolve the effective decision threshold from settings or model config."""
    if settings.decision_threshold is not None:
        return float(settings.decision_threshold)
    if predictor is not None:
        return float(predictor.config["optimal_threshold"])
    raise HTTPException(status_code=500, detail="No decision threshold configured")
