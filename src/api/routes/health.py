import time
from typing import Any, Dict

from fastapi import APIRouter, Request, Response, status
from src.config import settings
from src.inference.predictor import Predictor
from src.utils.circuit_breaker import CircuitBreaker

router = APIRouter()


@router.get("/health")
def health(request: Request, response: Response) -> Dict[str, Any]:
    predictor: Predictor | None = getattr(request.app.state, "predictor", None)
    breaker: CircuitBreaker | None = getattr(request.app.state, "breaker", None)

    is_healthy = predictor is not None
    
    health_status: Dict[str, Any] = {
        "status": "healthy" if is_healthy else "unhealthy",
        "model_loaded": predictor is not None,
        "service_degraded": False,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }

    if not is_healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        health_status["status"] = "unhealthy"

    if breaker:
        breaker_info: Dict[str, Any] = {
            "status": breaker.state,
            "failures": breaker.failure_count,
            "threshold": breaker.failure_threshold,
        }
        health_status["circuit_breaker"] = breaker_info
        if breaker.state != "closed":
            health_status["status"] = "degraded"
            health_status["service_degraded"] = True

    health_status["model_version"] = settings.model_version

    return health_status


@router.get("/model-info")
def model_info(request: Request) -> Dict[str, Any]:
    predictor: Predictor | None = getattr(request.app.state, "predictor", None)
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
        "decision_threshold": decision_threshold,
        "config_threshold": config_threshold,
        "positive_class": positive_class,
        "model_loaded": predictor is not None,
    }
