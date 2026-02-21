import csv
import io
import json
import logging
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.responses import StreamingResponse

from src.api.routes.predict import require_api_key
from src.config import settings
from src.inference.predictor import Predictor
from src.utils.metrics import Metrics

router = APIRouter(prefix="/v1")
logger = logging.getLogger(__name__)


@router.post("/batch")
async def batch_predict(
    req: Request,
    file: UploadFile = File(...),
    _: None = Depends(require_api_key),
) -> StreamingResponse:
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files accepted")

    content_length = req.headers.get("content-length")
    if content_length and int(content_length) > settings.max_csv_bytes:
        raise HTTPException(status_code=413, detail="CSV file too large")

    predictor: Predictor = req.app.state.predictor
    metrics: Metrics = req.app.state.metrics
    correlation_id = getattr(req.state, "correlation_id", None)
    if predictor is None:
        metrics.record_error()
        raise HTTPException(status_code=503, detail="Model unavailable")
    threshold = (
        float(settings.decision_threshold)
        if settings.decision_threshold is not None
        else float(predictor.config["optimal_threshold"])
    )

    # Create a wrapper that handles decoding properly
    # UploadFile.file is a SpooledTemporaryFile which is binary
    text_stream = io.TextIOWrapper(file.file, encoding="utf-8")

    # Check header first without reading whole file
    # We read the first line to check headers, then seek back
    first_line = text_stream.readline()
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

        batch_texts = []
        chunk_size = settings.max_batch_items

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

        for row in csv_reader:
            if "text" in row:
                batch_texts.append(row["text"])
                total_rows += 1

            if len(batch_texts) >= chunk_size:
                try:
                    labels, probs, latency = await predictor.apredict(
                        batch_texts, threshold
                    )
                except Exception:
                    metrics.record_error()
                    raise HTTPException(status_code=503, detail="Inference error")
                per_item_latency = latency / len(labels)

                for text, label, prob in zip(batch_texts, labels, probs):
                    clean_text = text.replace(",", " ").replace("\n", " ")[:100]
                    yield f"{clean_text},{label},{prob:.4f},{threshold:.4f},{_risk_level(float(prob))},{_recommended_action(float(prob), threshold)},{settings.model_version},{per_item_latency * 1000:.2f}\n"
                    metrics.record_prediction(label, per_item_latency)

                batch_texts = []

        # Process remaining
        if batch_texts:
            try:
                labels, probs, latency = await predictor.apredict(
                    batch_texts, threshold
                )
            except Exception:
                metrics.record_error()
                raise HTTPException(status_code=503, detail="Inference error")
            per_item_latency = latency / len(labels)
            for text, label, prob in zip(batch_texts, labels, probs):
                clean_text = text.replace(",", " ").replace("\n", " ")[:100]
                yield f"{clean_text},{label},{prob:.4f},{threshold:.4f},{_risk_level(float(prob))},{_recommended_action(float(prob), threshold)},{settings.model_version},{per_item_latency * 1000:.2f}\n"
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
