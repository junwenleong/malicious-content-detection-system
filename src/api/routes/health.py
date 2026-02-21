import time
from typing import Any, Dict, Optional

from fastapi import APIRouter, Request, Response, status
from src.config import settings
from src.inference.predictor import Predictor
from src.utils.circuit_breaker import CircuitBreaker

router = APIRouter()


@router.get("/health")
def health(request: Request, response: Response) -> Dict[str, Any]:
    predictor: Optional[Predictor] = getattr(request.app.state, "predictor", None)
    breaker: Optional[CircuitBreaker] = getattr(request.app.state, "breaker", None)

    is_healthy = predictor is not None
    
    health_status = {
        "status": "healthy" if is_healthy else "unhealthy",
        "model_loaded": predictor is not None,
        "service_degraded": False,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }

    if not is_healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        health_status["status"] = "unhealthy"

    if breaker:
        health_status["circuit_breaker"] = {
            "status": breaker.state,
            "failures": breaker.failure_count,
            "threshold": breaker.failure_threshold,
        }
        if breaker.state != "closed":
            health_status["status"] = "degraded"
            health_status["service_degraded"] = True
            # We don't necessarily fail health check for breaker open, 
            # as it might be temporary or partial degradation.
            # But if model is missing, it's definitely 503.

    return health_status


@router.get("/model-info")
def model_info(request: Request) -> Dict[str, Any]:
    predictor: Optional[Predictor] = getattr(request.app.state, "predictor", None)
    config_threshold = None
    positive_class = None
    if predictor:
        config_threshold = predictor.config.get("optimal_threshold")
        positive_class = predictor.config.get("positive_class")
    decision_threshold = (
        settings.decision_threshold
        if settings.decision_threshold is not None
        else config_threshold
    )
    return {
        "model_version": settings.model_version,
        "model_path": settings.model_path,
        "config_path": settings.config_path,
        "decision_threshold": decision_threshold,
        "config_threshold": config_threshold,
        "positive_class": positive_class,
        "model_loaded": predictor is not None,
    }
