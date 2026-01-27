from fastapi import FastAPI, HTTPException, Request, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, validator
from typing import List, Optional
import joblib
import os
import time
import logging
from collections import defaultdict
from datetime import datetime
import csv
import io

# --- Logging setup ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- Load model and config ---
MODEL_PATH = "models/malicious_content_detector_calibrated.pkl"
CONFIG_PATH = "models/malicious_content_detector_config.pkl"

if not os.path.exists(MODEL_PATH) or not os.path.exists(CONFIG_PATH):
    raise FileNotFoundError("Model files not found. Train the model first.")

model = joblib.load(MODEL_PATH)
config = joblib.load(CONFIG_PATH)
logger.info("Model and config loaded successfully")

app = FastAPI(
    title="Malicious Content Detection API",
    version="2.0",
    description=(
        "ML-based malicious content detection for agency's LLM. "
        "Provides real-time predictions and batch processing for abuse detection in text-based APIs. "
        "Model: TF-IDF + Calibrated Logistic Regression."
    )
)

# --- Metrics tracking ---
class Metrics:
    def __init__(self):
        self.total_requests = 0
        self.total_predictions = 0
        self.predictions_by_class = defaultdict(int)
        self.total_latency = 0.0
        self.errors = 0
        self.start_time = datetime.now()
    
    def record_prediction(self, label: str, latency: float):
        self.total_requests += 1
        self.total_predictions += 1
        self.predictions_by_class[label] += 1
        self.total_latency += latency
    
    def record_batch(self, labels: List[str], latency: float):
        self.total_requests += 1
        self.total_predictions += len(labels)
        for label in labels:
            self.predictions_by_class[label] += 1
        self.total_latency += latency
    
    def record_error(self):
        self.errors += 1
    
    def get_stats(self):
        uptime = (datetime.now() - self.start_time).total_seconds()
        avg_latency = self.total_latency / self.total_requests if self.total_requests > 0 else 0
        
        return {
            "uptime_seconds": uptime,
            "total_requests": self.total_requests,
            "total_predictions": self.total_predictions,
            "predictions_by_class": dict(self.predictions_by_class),
            "average_latency_ms": avg_latency * 1000,
            "errors": self.errors,
            "requests_per_second": self.total_requests / uptime if uptime > 0 else 0
        }

metrics = Metrics()

# --- Rate limiting (simple in-memory) ---
class RateLimiter:
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)
    
    def is_allowed(self, client_id: str) -> bool:
        now = time.time()
        # Clean old requests
        self.requests[client_id] = [
            req_time for req_time in self.requests[client_id]
            if now - req_time < self.window_seconds
        ]
        
        if len(self.requests[client_id]) >= self.max_requests:
            return False
        
        self.requests[client_id].append(now)
        return True

rate_limiter = RateLimiter(max_requests=100, window_seconds=60)

# --- Request/Response models ---
class PredictRequest(BaseModel):
    texts: List[str] = Field(..., min_items=1, max_items=100)
    
    @validator('texts')
    def validate_texts(cls, v):
        for text in v:
            if len(text) > 10000:  # Max 10k chars per text
                raise ValueError("Text exceeds maximum length of 10000 characters")
            if not text.strip():
                raise ValueError("Empty text not allowed")
        return v

class PredictionResult(BaseModel):
    text: str
    label: str
    probability_malicious: float
    threshold: float
    latency_ms: Optional[float] = None

class PredictResponse(BaseModel):
    predictions: List[PredictionResult]
    metadata: dict

# --- Core prediction function ---
def predict_malicious_content(texts: List[str]):
    """Predict malicious content labels and probabilities."""
    start_time = time.time()
    
    pos_class = config['positive_class']
    pos_index = list(model.classes_).index(pos_class)
    
    try:
        probs = model.predict_proba(texts)[:, pos_index]
        labels = ['MALICIOUS' if p >= config['optimal_threshold'] else 'BENIGN' for p in probs]
        
        latency = time.time() - start_time
        
        return labels, probs, latency
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        metrics.record_error()
        raise

# --- Middleware for logging ---
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Duration: {process_time*1000:.2f}ms"
    )
    
    return response

# --- Endpoints ---
@app.get("/")
def root():
    return {
        "message": "Malicious Content Detection API - Production Grade",
        "version": "2.0",
        "endpoints": {
            "predict": "/predict",
            "batch": "/batch",
            "health": "/health",
            "metrics": "/metrics",
            "docs": "/docs"
        }
    }

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "model_loaded": True,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/metrics")
def get_metrics():
    """Return system metrics for monitoring."""
    return metrics.get_stats()

@app.post("/predict", response_model=PredictResponse)
def predict(request: PredictRequest, req: Request):
    """Single or small batch prediction endpoint."""
    
    # Rate limiting
    client_ip = req.client.host
    if not rate_limiter.is_allowed(client_ip):
        logger.warning(f"Rate limit exceeded for {client_ip}")
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Max 100 requests per minute.")
    
    try:
        labels, probs, latency = predict_malicious_content(request.texts)
        
        # Record metrics
        for label in labels:
            metrics.record_prediction(label, latency / len(labels))
        
        predictions = [
            PredictionResult(
                text=text[:100] + "..." if len(text) > 100 else text,  # Truncate in response
                label=label,
                probability_malicious=float(prob),
                threshold=config['optimal_threshold'],
                latency_ms=latency * 1000 / len(labels)
            )
            for text, label, prob in zip(request.texts, labels, probs)
        ]
        
        logger.info(f"Predicted {len(predictions)} texts. Labels: {labels}")
        
        return PredictResponse(
            predictions=predictions,
            metadata={
                "total_items": len(predictions),
                "malicious_count": sum(1 for label in labels if label == 'MALICIOUS'),
                "benign_count": sum(1 for label in labels if label == 'BENIGN'),
                "total_latency_ms": latency * 1000
            }
        )
    
    except Exception as e:
        logger.error(f"Prediction failed: {str(e)}")
        metrics.record_error()
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")

@app.post("/batch")
async def batch_predict(file: UploadFile = File(...)):
    """
    Batch prediction from CSV file.
    
    Expected CSV format:
    text
    "First text to analyze"
    "Second text to analyze"
    ...
    
    Returns CSV with predictions.
    """
    
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files accepted")
    
    try:
        # Read CSV
        contents = await file.read()
        df_input = io.StringIO(contents.decode('utf-8'))
        
        texts = []
        csv_reader = csv.DictReader(df_input)
        
        for row in csv_reader:
            if 'text' not in row:
                raise HTTPException(status_code=400, detail="CSV must have 'text' column")
            texts.append(row['text'])
        
        if not texts:
            raise HTTPException(status_code=400, detail="No texts found in CSV")
        
        logger.info(f"Processing batch of {len(texts)} texts from {file.filename}")
        
        # Predict
        labels, probs, latency = predict_malicious_content(texts)
        
        # Record metrics
        metrics.record_batch(labels, latency)
        
        # Create response CSV
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['text', 'label', 'probability_malicious', 'threshold'])
        
        for text, label, prob in zip(texts, labels, probs):
            writer.writerow([text, label, f"{prob:.4f}", config['optimal_threshold']])
        
        output.seek(0)
        
        logger.info(f"Batch processing complete. {len(texts)} predictions made.")
        
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=predictions_{file.filename}"}
        )
    
    except Exception as e:
        logger.error(f"Batch prediction failed: {str(e)}")
        metrics.record_error()
        raise HTTPException(status_code=500, detail=f"Batch processing error: {str(e)}")
