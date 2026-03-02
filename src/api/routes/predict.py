import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from src.api.schemas import PredictRequest, PredictResponse, PredictionResult
from src.api.dependencies import (
    require_api_key,
    resolve_threshold,
    get_predictor,
    get_metrics,
    get_circuit_breaker,
    check_rate_limit,
    check_circuit_breaker,
)
from src.api.auth import verify_signature
from src.config import settings
from src.inference.base import BasePredictor
from src.inference.fallback import FallbackPredictor
from src.utils.circuit_breaker import CircuitBreaker
from src.utils.metrics import Metrics
from src.utils.policy import policy_decision
from src.utils.text import hash_text

router = APIRouter(prefix="/v1")
logger = logging.getLogger(__name__)

_fallback = FallbackPredictor()


@router.post(
    "/predict", response_model=PredictResponse, dependencies=[Depends(verify_signature)]
)
async def predict(
    request: PredictRequest,
    req: Request,
    _: None = Depends(require_api_key),
    __: None = Depends(check_rate_limit),
    ___: None = Depends(check_circuit_breaker),
) -> PredictResponse:
    # Defensive: Strip whitespace (Pydantic already rejects empty strings,
    # but stripping ensures consistent normalization before inference)
    texts = [text.strip() for text in request.texts]

    if len(texts) > settings.max_batch_items:
        raise HTTPException(status_code=400, detail="Batch size exceeds maximum items")
    if any(len(text) > settings.max_text_length for text in texts):
        raise HTTPException(status_code=400, detail="Text exceeds maximum length")

    # Get dependencies
    predictor: BasePredictor = get_predictor(req)
    metrics: Metrics = get_metrics(req)
    breaker: CircuitBreaker | None = get_circuit_breaker(req)
    threshold = resolve_threshold(predictor)
    used_fallback = False
    try:
        labels, probs, latency = await predictor.apredict(texts, threshold)
        if breaker:
            breaker.record_success()
    except Exception as e:
        logger.error(f"Prediction error: {e}", exc_info=True)
        if breaker:
            breaker.record_failure()
        metrics.record_error()
        # Attempt fallback before returning 503
        try:
            labels, probs, latency = _fallback.predict_safe_fallback(texts, threshold)
            used_fallback = True
            logger.warning(
                json.dumps(
                    {
                        "event": "fallback_activated",
                        "correlation_id": getattr(req.state, "correlation_id", None),
                        "text_count": len(texts),
                    }
                )
            )
        except Exception:
            raise HTTPException(status_code=503, detail="Inference error")
    per_item_latency = latency / max(len(labels), 1)
    for label in labels:
        metrics.record_prediction(label, per_item_latency)

    predictions = []
    for text, label, prob in zip(texts, labels, probs):
        risk_level, recommended_action = policy_decision(float(prob), threshold)
        predictions.append(
            PredictionResult(
                text_hash=hash_text(text),
                label=str(label),
                probability_malicious=float(prob),
                threshold=threshold,
                risk_level=risk_level,
                recommended_action=recommended_action,
                latency_ms=per_item_latency * 1000,
                is_fallback=used_fallback,
            )
        )
    logger.info(
        json.dumps(
            {
                "event": "predict_completed",
                "correlation_id": getattr(req.state, "correlation_id", None),
                "text_count": len(texts),
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
            "unknown_count": sum(1 for label in labels if label == "UNKNOWN"),
            "total_latency_ms": latency * 1000,
            "model_version": settings.model_version,
        },
    )
