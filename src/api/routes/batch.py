import csv
import io
import json
import logging
from typing import AsyncGenerator, List, Tuple

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.responses import StreamingResponse

from src.api.dependencies import (
    require_api_key,
    resolve_threshold,
    get_predictor,
    get_metrics,
    get_circuit_breaker,
    check_rate_limit,
    check_circuit_breaker,
)
from src.utils.text import hash_text
from src.config import settings
from src.inference.base import BasePredictor
from src.utils.circuit_breaker import CircuitBreaker
from src.utils.metrics import Metrics
from src.utils.policy import policy_decision

router = APIRouter(prefix="/v1")
logger = logging.getLogger(__name__)


def _validate_csv_file(file: UploadFile, content_length: str | None) -> None:
    """Validate CSV file format and size."""
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

    if content_length and int(content_length) > settings.max_csv_bytes:
        raise HTTPException(status_code=413, detail="CSV file too large")


def _validate_csv_header(text_stream: io.TextIOWrapper) -> None:
    """Validate CSV has required 'text' column."""
    try:
        text_stream.seek(0)
        csv_reader = csv.DictReader(text_stream)
        if not csv_reader.fieldnames or "text" not in csv_reader.fieldnames:
            raise HTTPException(status_code=400, detail="CSV must have 'text' column")
        text_stream.seek(0)
    except UnicodeDecodeError as e:
        raise HTTPException(
            status_code=400, detail=f"Invalid UTF-8 encoding in file: {str(e)}"
        )


async def _process_batch(
    batch_texts: List[str],
    predictor: BasePredictor,
    threshold: float,
    breaker: CircuitBreaker | None,
    metrics: Metrics,
    correlation_id: str | None,
) -> Tuple[List[str], List[float], float] | None:
    """Process a batch of texts and return predictions or None on error."""
    try:
        labels, probs, latency = await predictor.apredict(batch_texts, threshold)
        if breaker:
            breaker.record_success()
        return labels, probs, latency
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
                }
            )
        )
        return None


def _sanitize_csv_cell(value: str) -> str:
    """Sanitize a CSV cell value to prevent formula injection.

    Cells starting with =, +, -, @, TAB, CR are prefixed with a single quote
    to prevent spreadsheet applications from interpreting them as formulas.

    Args:
        value: Raw cell value

    Returns:
        Sanitized cell value safe for CSV output
    """
    if value and value[0] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + value
    return value


def _format_csv_row(
    text: str,
    label: str,
    prob: float,
    threshold: float,
    per_item_latency: float,
) -> str:
    """Format a single prediction result as CSV row."""
    text_hash = hash_text(text)
    risk_level, recommended_action = policy_decision(float(prob), threshold)
    # Sanitize label and action fields against CSV formula injection
    safe_label = _sanitize_csv_cell(label)
    safe_risk = _sanitize_csv_cell(risk_level)
    safe_action = _sanitize_csv_cell(recommended_action)
    safe_version = _sanitize_csv_cell(settings.model_version)
    return f"{text_hash},{safe_label},{prob:.4f},{threshold:.4f},{safe_risk},{safe_action},{safe_version},{per_item_latency * 1000:.2f}\n"


@router.post("/batch")
async def batch_predict(
    req: Request,
    file: UploadFile = File(...),
    _: None = Depends(require_api_key),
    __: None = Depends(check_rate_limit),
    ___: None = Depends(check_circuit_breaker),
) -> StreamingResponse:
    """Process CSV file with batch predictions."""
    content_length = req.headers.get("content-length")
    _validate_csv_file(file, content_length)

    # Get dependencies
    predictor: BasePredictor = get_predictor(req)
    metrics: Metrics = get_metrics(req)
    breaker: CircuitBreaker | None = get_circuit_breaker(req)
    correlation_id = getattr(req.state, "correlation_id", None)
    threshold = resolve_threshold(predictor)

    # Create text stream wrapper
    try:
        text_stream = io.TextIOWrapper(file.file, encoding="utf-8", errors="strict")
    except UnicodeDecodeError as e:
        raise HTTPException(
            status_code=400, detail=f"Invalid UTF-8 encoding in file: {str(e)}"
        )

    _validate_csv_header(text_stream)
    csv_reader = csv.DictReader(text_stream)

    total_rows = 0
    MAX_TOTAL_ROWS = settings.max_batch_items * 100  # hard cap: 100 chunks max

    async def generate() -> AsyncGenerator[str, None]:
        nonlocal total_rows
        yield "text_hash,label,probability,threshold,risk_level,recommended_action,model_version,latency_ms\n"

        batch_texts: list[str] = []
        chunk_size = settings.max_batch_items

        try:
            for row in csv_reader:
                if "text" not in row:
                    continue

                # Check limit BEFORE appending to prevent processing rows beyond cap
                if total_rows >= MAX_TOTAL_ROWS:
                    logger.warning(
                        json.dumps(
                            {
                                "event": "batch_row_limit_exceeded",
                                "correlation_id": correlation_id,
                                "max_rows": MAX_TOTAL_ROWS,
                            }
                        )
                    )
                    # Flush any pending batch before emitting the error sentinel
                    if batch_texts:
                        result = await _process_batch(
                            batch_texts,
                            predictor,
                            threshold,
                            breaker,
                            metrics,
                            correlation_id,
                        )
                        if result is not None:
                            labels, probs, latency = result
                            per_item_latency = latency / max(len(labels), 1)
                            for text, label, prob in zip(batch_texts, labels, probs):
                                yield _format_csv_row(
                                    text, label, prob, threshold, per_item_latency
                                )
                                metrics.record_prediction(label, per_item_latency)
                        batch_texts = []
                    yield f"ERROR,ROW_LIMIT_EXCEEDED,0,0,ERROR,ERROR,{settings.model_version},0\n"
                    return

                batch_texts.append(row["text"])
                total_rows += 1

                if len(batch_texts) >= chunk_size:
                    result = await _process_batch(
                        batch_texts,
                        predictor,
                        threshold,
                        breaker,
                        metrics,
                        correlation_id,
                    )
                    if result is None:
                        yield f"ERROR,INFERENCE_FAILED,0,0,ERROR,ERROR,{settings.model_version},0\n"
                        return

                    labels, probs, latency = result
                    per_item_latency = latency / max(len(labels), 1)

                    for text, label, prob in zip(batch_texts, labels, probs):
                        yield _format_csv_row(
                            text, label, prob, threshold, per_item_latency
                        )
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

        # Process remaining batch
        if batch_texts:
            result = await _process_batch(
                batch_texts, predictor, threshold, breaker, metrics, correlation_id
            )
            if result is None:
                yield f"ERROR,INFERENCE_FAILED,0,0,ERROR,ERROR,{settings.model_version},0\n"
                return

            labels, probs, latency = result
            per_item_latency = latency / max(len(labels), 1)

            for text, label, prob in zip(batch_texts, labels, probs):
                yield _format_csv_row(text, label, prob, threshold, per_item_latency)
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
