from typing import List, Optional, Any, Dict

from pydantic import BaseModel, Field, field_validator

from src.config import settings


class PredictRequest(BaseModel):
    texts: List[str] = Field(..., min_length=1, max_length=settings.max_batch_items)

    @field_validator("texts")
    @classmethod
    def validate_texts(cls, value: List[str]) -> List[str]:
        for text in value:
            if not isinstance(text, str) or not text.strip():
                raise ValueError("Empty text not allowed")
            if len(text) > settings.max_text_length:
                raise ValueError(
                    f"Text exceeds maximum length of {settings.max_text_length} characters"
                )
        return value


class PredictionResult(BaseModel):
    text_hash: str = Field(
        ..., description="SHA256 hash of input text (for audit trail, not raw text)"
    )
    label: str
    probability_malicious: float
    threshold: float
    risk_level: str
    recommended_action: str
    latency_ms: Optional[float] = None
    is_fallback: bool = Field(
        default=False,
        description="True when prediction was produced by the fallback predictor (primary model unavailable). Treat with lower confidence.",
    )


class PredictResponse(BaseModel):
    predictions: List[PredictionResult]
    metadata: Dict[str, Any]
