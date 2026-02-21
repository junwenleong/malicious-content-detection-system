import hashlib
import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from src.api.schemas import PredictRequest, PredictResponse, PredictionResult
from src.config import settings
from src.inference.predictor import Predictor
from src.utils.circuit_breaker import CircuitBreaker
from src.utils.metrics import Metrics
from src.utils.policy import policy_decision
from src.utils.rate_limiter import RateLimiter
from src.api.auth import verify_signature

router = APIRouter(prefix="/v1")
logger = logging.getLogger(__name__)


def require_api_key(request: Request) -> None:
    # 1. Ensure API Key is Configured (Security Fix: Prevent Bypass)
    if not settings.api_keys:
        logger.error("API Keys not configured in settings")
        raise HTTPException(status_code=500, detail="Server configuration error: No API keys configured")

    # 2. Rate Limiting for Auth Failures
    client_ip = request.client.host if request.client else "unknown"
    # Access auth_rate_limiter from app state
    try:
        auth_limiter: RateLimiter = request.app.state.auth_rate_limiter
    except AttributeError:
        # Fallback if not initialized (e.g. tests)
        logger.warning("Auth rate limiter not initialized")
        auth_limiter = RateLimiter(5, 60)

    if auth_limiter.is_blocked(client_ip):
        logger.warning(
            json.dumps({
                "event": "auth_rate_limit_exceeded",
                "client_ip": client_ip,
                "correlation_id": getattr(request.state, "correlation_id", None)
            })
        )
        raise HTTPException(status_code=429, detail="Too many authentication attempts")

    # 3. Validate Key
    provided = request.headers.get("x-api-key", "")
    if provided not in settings.api_keys:
        auth_limiter.record_attempt(client_ip)
        logger.warning(
            json.dumps({
                "event": "invalid_api_key",
                "client_ip": client_ip,
                "correlation_id": getattr(request.state, "correlation_id", None)
            })
        )
        raise HTTPException(status_code=403, detail="Invalid API key")


def _hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


@router.post("/predict", response_model=PredictResponse, dependencies=[Depends(verify_signature)])
async def predict(
    request: PredictRequest,
    req: Request,
    _: None = Depends(require_api_key),
) -> PredictResponse:
    if not req.client or not req.client.host:
        raise HTTPException(status_code=400, detail="Could not determine client IP")

    client_ip = req.client.host
    rate_limiter: RateLimiter = req.app.state.rate_limiter
    if not rate_limiter.is_allowed(client_ip):
        logger.warning(
            json.dumps(
                {
                    "event": "rate_limit_exceeded",
                    "correlation_id": getattr(req.state, "correlation_id", None),
                    "client_ip": client_ip,
                }
            )
        )
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    texts = [text.strip() for text in request.texts]
    if not texts:
        # Should be caught by pydantic, but defensive programming
        return PredictResponse(predictions=[], metadata={})

    if len(texts) > settings.max_batch_items:
        raise HTTPException(status_code=400, detail="Batch size exceeds maximum items")
    if any(len(text) > settings.max_text_length for text in texts):
        raise HTTPException(status_code=400, detail="Text exceeds maximum length")

    metrics: Metrics = req.app.state.metrics
    breaker: CircuitBreaker | None = getattr(req.app.state, "breaker", None)
    if breaker and not breaker.allow_request():
        metrics.record_error()
        raise HTTPException(status_code=503, detail="Inference temporarily unavailable")
    predictor: Predictor = req.app.state.predictor
    if predictor is None:
        metrics.record_error()
        raise HTTPException(status_code=503, detail="Model unavailable")

    threshold = (
        float(settings.decision_threshold)
        if settings.decision_threshold is not None
        else float(predictor.config["optimal_threshold"])
    )
    try:
        labels, probs, latency = await predictor.apredict(texts, threshold)
    except Exception as e:
        logger.error(f"Prediction error: {e}", exc_info=True)
        if breaker:
            breaker.record_failure()
        metrics.record_error()
        raise HTTPException(status_code=503, detail="Inference error")
    if breaker:
        breaker.record_success()

    per_item_latency = latency / max(len(labels), 1)
    for label in labels:
        metrics.record_prediction(label, per_item_latency)

    predictions = []
    for text, label, prob in zip(texts, labels, probs):
        risk_level, recommended_action = policy_decision(float(prob), threshold)
        predictions.append(
            PredictionResult(
                text=text[:100] + "..." if len(text) > 100 else text,
                label=str(label),
                probability_malicious=float(prob),
                threshold=threshold,
                risk_level=risk_level,
                recommended_action=recommended_action,
                latency_ms=per_item_latency * 1000,
            )
        )
    logger.info(
        json.dumps(
            {
                "event": "predict_completed",
                "correlation_id": getattr(req.state, "correlation_id", None),
                "text_count": len(texts),
                "text_hashes": [_hash_text(text) for text in texts[:5]],
                "decision_threshold": threshold,
                "latency_ms": round(latency * 1000, 2),
            }
        )
    )

    return PredictResponse(
        predictions=predictions,
        metadata={
            "total_items": len(predictions),
            "malicious_count": sum(1 for label in labels if label == "MALICIOUS"),
            "benign_count": sum(1 for label in labels if label == "BENIGN"),
            "total_latency_ms": latency * 1000,
            "model_version": settings.model_version,
        },
    )
