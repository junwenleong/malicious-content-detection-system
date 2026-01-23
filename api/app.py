from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import joblib
from typing import List
import os

# --- Load model and config ---
MODEL_PATH = "abuse_detector_calibrated.pkl"
CONFIG_PATH = "abuse_detector_config.pkl"

if not os.path.exists(MODEL_PATH) or not os.path.exists(CONFIG_PATH):
    raise FileNotFoundError("Model files not found. Train the model first.")

model = joblib.load(MODEL_PATH)
config = joblib.load(CONFIG_PATH)

app = FastAPI(title="Abuse Detection API", version="1.0")

# --- Request/Response models ---
class PredictRequest(BaseModel):
    texts: List[str]

class PredictResponse(BaseModel):
    predictions: List[dict]

# --- Prediction function ---
def predict_abuse(texts):
    """Predict abuse labels and probabilities."""
    pos_class = config['positive_class']
    pos_index = list(model.classes_).index(pos_class)
    
    probs = model.predict_proba(texts)[:, pos_index]
    labels = ['ABUSIVE' if p >= config['optimal_threshold'] else 'BENIGN' for p in probs]
    
    return labels, probs

# --- Endpoints ---
@app.get("/")
def root():
    return {
        "message": "Abuse Detection API",
        "version": "1.0",
        "endpoints": ["/predict", "/health"]
    }

@app.get("/health")
def health():
    return {"status": "healthy", "model_loaded": True}

@app.post("/predict", response_model=PredictResponse)
def predict(request: PredictRequest):
    if not request.texts:
        raise HTTPException(status_code=400, detail="No texts provided")
    
    labels, probs = predict_abuse(request.texts)
    
    predictions = [
        {
            "text": text,
            "label": label,
            "probability_abusive": float(prob),
            "threshold": config['optimal_threshold']
        }
        for text, label, prob in zip(request.texts, labels, probs)
    ]
    
    return {"predictions": predictions}
