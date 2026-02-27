"""Metrics endpoint for Prometheus scraping."""

from fastapi import APIRouter, Request
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response

router = APIRouter()


@router.get("/metrics")
def metrics_endpoint(request: Request) -> Response:
    """Expose Prometheus metrics for scraping."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
