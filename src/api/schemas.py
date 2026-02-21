from typing import List, Optional, Any, Dict

from pydantic import BaseModel, Field, field_validator


class PredictRequest(BaseModel):
    texts: List[str] = Field(..., min_length=1, max_length=1000)

    @field_validator("texts")
    @classmethod
    def validate_texts(cls, value: List[str]) -> List[str]:
        for text in value:
            if not isinstance(text, str) or not text.strip():
                raise ValueError("Empty text not allowed")
        return value


class PredictionResult(BaseModel):
    text: str
    label: str
    probability_malicious: float
    threshold: float
    risk_level: str
    recommended_action: str
    latency_ms: Optional[float] = None


class PredictResponse(BaseModel):
    predictions: List[PredictionResult]
    metadata: Dict[str, Any]
