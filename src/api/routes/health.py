import time
from typing import Any, Dict, Optional, cast

from fastapi import APIRouter, Request
from fastapi.responses import Response
from src.config import settings
from src.inference.predictor import Predictor
from src.utils.metrics import Metrics

router = APIRouter()


@router.get("/health")
def health(request: Request) -> Dict[str, Any]:
    predictor: Optional[Predictor] = getattr(request.app.state, "predictor", None)
    return {
        "status": "healthy",
        "model_loaded": predictor is not None,
        "service_degraded": predictor is None,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }


@router.get("/metrics")
def get_metrics(request: Request) -> Dict[str, Any]:
    metrics = cast(Metrics, request.app.state.metrics)
    return metrics.get_stats()


@router.get("/metrics/prometheus")
def get_metrics_prometheus(request: Request) -> Response:
    metrics = cast(Metrics, request.app.state.metrics)
    stats = metrics.get_stats()
    lines = []
    lines.append("# HELP abuse_uptime_seconds Service uptime in seconds")
    lines.append("# TYPE abuse_uptime_seconds gauge")
    lines.append(f"abuse_uptime_seconds {stats['uptime_seconds']}")
    lines.append("# HELP abuse_total_requests Total request count")
    lines.append("# TYPE abuse_total_requests counter")
    lines.append(f"abuse_total_requests {stats['total_requests']}")
    lines.append("# HELP abuse_total_predictions Total predictions count")
    lines.append("# TYPE abuse_total_predictions counter")
    lines.append(f"abuse_total_predictions {stats['total_predictions']}")
    labels = cast(Dict[str, int], stats.get("predictions_by_class", {}))
    for k, v in labels.items():
        lines.append(
            "# HELP abuse_predictions_by_class_total Total predictions by class"
        )
        lines.append("# TYPE abuse_predictions_by_class_total counter")
        lines.append(f'abuse_predictions_by_class_total{{label="{k}"}} {v}')
    lines.append("# HELP abuse_average_latency_ms Average latency in ms")
    lines.append("# TYPE abuse_average_latency_ms gauge")
    lines.append(f"abuse_average_latency_ms {stats['average_latency_ms']}")
    lines.append("# HELP abuse_errors_total Total errors")
    lines.append("# TYPE abuse_errors_total counter")
    lines.append(f"abuse_errors_total {stats['errors']}")
    lines.append("# HELP abuse_requests_per_second Requests per second")
    lines.append("# TYPE abuse_requests_per_second gauge")
    lines.append(f"abuse_requests_per_second {stats['requests_per_second']}")
    payload = "\n".join(lines) + "\n"
    return Response(content=payload, media_type="text/plain; charset=utf-8")


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
