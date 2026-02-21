import hashlib
import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from src.api.schemas import PredictRequest, PredictResponse, PredictionResult
from src.config import settings
from src.inference.predictor import Predictor
from src.utils.metrics import Metrics
from src.utils.rate_limiter import RateLimiter

router = APIRouter(prefix="/v1")
logger = logging.getLogger(__name__)


def require_api_key(request: Request) -> None:
    if not settings.api_key:
        return
    provided = request.headers.get("x-api-key", "")
    if provided != settings.api_key:
        raise HTTPException(status_code=403, detail="Invalid API key")


def _hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


@router.post("/predict", response_model=PredictResponse)
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
    if len(texts) > settings.max_batch_items:
        raise HTTPException(status_code=400, detail="Batch size exceeds maximum items")
    if any(len(text) > settings.max_text_length for text in texts):
        raise HTTPException(status_code=400, detail="Text exceeds maximum length")

    metrics: Metrics = req.app.state.metrics
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
    except Exception:
        metrics.record_error()
        raise HTTPException(status_code=503, detail="Inference error")

    per_item_latency = latency / max(len(labels), 1)
    for label in labels:
        metrics.record_prediction(label, per_item_latency)

    def _risk_level(prob: float) -> str:
        if prob >= 0.85:
            return "HIGH"
        if prob >= 0.6:
            return "MEDIUM"
        return "LOW"

    def _recommended_action(prob: float, th: float) -> str:
        if prob >= th + 0.15:
            return "BLOCK"
        if prob >= th:
            return "REVIEW"
        return "ALLOW"

    predictions = [
        PredictionResult(
            text=text[:100] + "..." if len(text) > 100 else text,
            label=str(label),
            probability_malicious=float(prob),
            threshold=threshold,
            risk_level=_risk_level(float(prob)),
            recommended_action=_recommended_action(float(prob), threshold),
            latency_ms=per_item_latency * 1000,
        )
        for text, label, prob in zip(texts, labels, probs)
    ]
    logger.info(
        json.dumps(
            {
                "event": "predict_completed",
                "correlation_id": getattr(req.state, "correlation_id", None),
                "text_count": len(texts),
                "text_hashes": [_hash_text(text) for text in texts][:5],
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
