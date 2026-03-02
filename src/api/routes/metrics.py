"""Metrics endpoint for Prometheus scraping."""

from fastapi import APIRouter, Depends, Request
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response

from src.api.dependencies import require_api_key

router = APIRouter()


@router.get("/metrics", dependencies=[Depends(require_api_key)])
def metrics_endpoint(request: Request) -> Response:
    """Expose Prometheus metrics for scraping. Requires API key authentication."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
