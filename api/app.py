import json
import logging
import time
import uuid
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Dict, List, cast

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastui import FastUI

from src.api.fastui import ui_landing, ui_root
from src.config import settings
from src.inference.predictor import Predictor
from src.utils.metrics import Metrics
from src.utils.rate_limiter import RateLimiter

# Import routers
from src.api.routes import health, predict, batch

logging.basicConfig(
    level=logging.INFO,
    format='{"time":"%(asctime)s","name":"%(name)s","level":"%(levelname)s","message":"%(message)s"}',
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    try:
        app.state.predictor = Predictor(settings.model_path, settings.config_path)
    except Exception:
        app.state.predictor = None
    app.state.metrics = Metrics()
    app.state.rate_limiter = RateLimiter(
        settings.rate_limit_max, settings.rate_limit_window
    )
    yield


app = FastAPI(
    title="Malicious Content Detection API",
    version="3.0",
    description=(
        "ML-based malicious content detection for agency's LLM. "
        "Provides real-time predictions and batch processing for abuse detection in text-based APIs. "
        "Model: TF-IDF + Calibrated Logistic Regression."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next: Any) -> Response:
    correlation_id = (
        request.headers.get("x-correlation-id")
        or request.headers.get("x-request-id")
        or str(uuid.uuid4())
    )
    request.state.correlation_id = correlation_id
    start_time = time.time()
    try:
        response = await call_next(request)
    except Exception:
        process_time = time.time() - start_time
        logger.error(
            json.dumps(
                {
                    "event": "request_error",
                    "correlation_id": correlation_id,
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": round(process_time * 1000, 2),
                }
            )
        )
        raise
    process_time = time.time() - start_time
    response.headers["x-correlation-id"] = correlation_id
    logger.info(
        json.dumps(
            {
                "event": "request_completed",
                "correlation_id": correlation_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(process_time * 1000, 2),
            }
        )
    )
    return cast(Response, response)


# Include Routers
app.include_router(health.router)
app.include_router(predict.router)
app.include_router(batch.router)


@app.get("/")
def root() -> Dict[str, Any]:
    return {
        "message": "Malicious Content Detection API - Production Grade",
        "version": "3.0",
        "endpoints": {
            "predict": "/v1/predict",
            "batch": "/v1/batch",
            "health": "/health",
            "metrics": "/metrics",
            "model_info": "/model-info",
            "docs": "/docs",
        },
    }


@app.get("/fastui/api", response_model=FastUI, response_model_exclude_none=True)
def fastui_api() -> List[Any]:
    if not settings.fastui_enabled:
        raise HTTPException(status_code=404, detail="FastUI disabled")
    return ui_root()


@app.get("/fastui")
def fastui_html() -> Any:
    if not settings.fastui_enabled:
        raise HTTPException(status_code=404, detail="FastUI disabled")
    return ui_landing()
