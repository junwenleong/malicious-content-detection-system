import csv
import io
import json
import logging
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.responses import StreamingResponse

from src.api.dependencies import require_api_key, resolve_threshold
from src.config import settings
from src.inference.predictor import Predictor
from src.utils.circuit_breaker import CircuitBreaker
from src.utils.metrics import Metrics
from src.utils.policy import policy_decision
from src.utils.rate_limiter import RateLimiter

router = APIRouter(prefix="/v1")
logger = logging.getLogger(__name__)


@router.post("/batch")
async def batch_predict(
    req: Request,
    file: UploadFile = File(...),
    _: None = Depends(require_api_key),
) -> StreamingResponse:
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only .csv files accepted")

    # MIME Type Validation
    allowed_mime_types = {
        "text/csv",
        "application/vnd.ms-excel",
        "application/csv",
        "text/plain",
        None,
    }
    if file.content_type not in allowed_mime_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid content type: {file.content_type}. Only CSV allowed.",
        )

    content_length = req.headers.get("content-length")
    if content_length and int(content_length) > settings.max_csv_bytes:
        raise HTTPException(status_code=413, detail="CSV file too large")

    metrics: Metrics = req.app.state.metrics
    breaker: CircuitBreaker | None = getattr(req.app.state, "breaker", None)
    if breaker and not breaker.allow_request():
        metrics.record_error()
        raise HTTPException(status_code=503, detail="Inference temporarily unavailable")
    predictor: Predictor = req.app.state.predictor
    correlation_id = getattr(req.state, "correlation_id", None)
    if predictor is None:
        metrics.record_error()
        raise HTTPException(status_code=503, detail="Model unavailable")

    # Rate limit batch requests
    client_ip = req.client.host if req.client else "unknown"
    rate_limiter: RateLimiter = req.app.state.rate_limiter
    if not rate_limiter.is_allowed(client_ip):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded",
            headers={"Retry-After": str(settings.rate_limit_window)},
        )

    threshold = resolve_threshold(predictor)

    # Create a wrapper that handles decoding properly
    # UploadFile.file is a SpooledTemporaryFile which is binary
    try:
        text_stream = io.TextIOWrapper(file.file, encoding="utf-8", errors="strict")
    except UnicodeDecodeError as e:
        raise HTTPException(
            status_code=400, detail=f"Invalid UTF-8 encoding in file: {str(e)}"
        )

    # Check header first without reading whole file
    # We read the first line to check headers, then seek back
    try:
        first_line = text_stream.readline()
    except UnicodeDecodeError as e:
        raise HTTPException(
            status_code=400, detail=f"Invalid UTF-8 encoding in file: {str(e)}"
        )

    if not first_line:
        raise HTTPException(status_code=400, detail="Empty file")

    # Simple check for 'text' column in header
    if "text" not in first_line:
        # Try to parse as CSV to be sure, but this is a quick fail
        # Reset and use DictReader properly
        text_stream.seek(0)
        csv_reader = csv.DictReader(text_stream)
        if not csv_reader.fieldnames or "text" not in csv_reader.fieldnames:
            raise HTTPException(status_code=400, detail="CSV must have 'text' column")

    text_stream.seek(0)
    csv_reader = csv.DictReader(text_stream)

    total_rows = 0

    async def generate() -> AsyncGenerator[str, None]:
        nonlocal total_rows
        yield "text,label,probability,threshold,risk_level,recommended_action,model_version,latency_ms\n"

        batch_texts: list[str] = []
        chunk_size = settings.max_batch_items

        try:
            for row in csv_reader:
                if "text" in row:
                    batch_texts.append(row["text"])
                    total_rows += 1

                if len(batch_texts) >= chunk_size:
                    try:
                        labels, probs, latency = await predictor.apredict(
                            batch_texts, threshold
                        )
                    except Exception as exc:
                        if breaker:
                            breaker.record_failure()
                        metrics.record_error()
                        logger.error(
                            json.dumps(
                                {
                                    "event": "batch_inference_error",
                                    "correlation_id": correlation_id,
                                    "error": str(exc)[:500],
                                    "rows_processed": total_rows,
                                }
                            )
                        )
                        yield f"ERROR,INFERENCE_FAILED,0,0,ERROR,ERROR,{settings.model_version},0\n"
                        return
                    if breaker:
                        breaker.record_success()
                    per_item_latency = latency / max(len(labels), 1)

                    for text, label, prob in zip(batch_texts, labels, probs):
                        clean_text = text.replace(",", " ").replace("\n", " ")[:100]
                        risk_level, recommended_action = policy_decision(
                            float(prob), threshold
                        )
                        yield f"{clean_text},{label},{prob:.4f},{threshold:.4f},{risk_level},{recommended_action},{settings.model_version},{per_item_latency * 1000:.2f}\n"
                        metrics.record_prediction(label, per_item_latency)

                    batch_texts = []
        except UnicodeDecodeError as e:
            logger.error(
                json.dumps(
                    {
                        "event": "batch_encoding_error",
                        "correlation_id": correlation_id,
                        "error": str(e)[:500],
                        "rows_processed": total_rows,
                    }
                )
            )
            yield f"ERROR,ENCODING_ERROR,0,0,ERROR,ERROR,{settings.model_version},0\n"
            return
        except csv.Error as e:
            logger.error(
                json.dumps(
                    {
                        "event": "batch_csv_error",
                        "correlation_id": correlation_id,
                        "error": str(e)[:500],
                        "rows_processed": total_rows,
                    }
                )
            )
            yield f"ERROR,CSV_PARSE_ERROR,0,0,ERROR,ERROR,{settings.model_version},0\n"
            return

        # Process remaining
        if batch_texts:
            try:
                labels, probs, latency = await predictor.apredict(
                    batch_texts, threshold
                )
            except Exception as exc:
                if breaker:
                    breaker.record_failure()
                metrics.record_error()
                logger.error(
                    json.dumps(
                        {
                            "event": "batch_inference_error",
                            "correlation_id": correlation_id,
                            "error": str(exc)[:500],
                            "rows_processed": total_rows,
                        }
                    )
                )
                yield f"ERROR,INFERENCE_FAILED,0,0,ERROR,ERROR,{settings.model_version},0\n"
                return
            if breaker:
                breaker.record_success()
            per_item_latency = latency / max(len(labels), 1)
            for text, label, prob in zip(batch_texts, labels, probs):
                clean_text = text.replace(",", " ").replace("\n", " ")[:100]
                risk_level, recommended_action = policy_decision(float(prob), threshold)
                yield f"{clean_text},{label},{prob:.4f},{threshold:.4f},{risk_level},{recommended_action},{settings.model_version},{per_item_latency * 1000:.2f}\n"
                metrics.record_prediction(label, per_item_latency)
        logger.info(
            json.dumps(
                {
                    "event": "batch_completed",
                    "correlation_id": correlation_id,
                    "row_count": total_rows,
                    "decision_threshold": threshold,
                }
            )
        )

    return StreamingResponse(generate(), media_type="text/csv")
