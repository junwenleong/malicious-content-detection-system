# Malicious Content Detection System

**A ML system for detecting abusive content for deployment over text-based APIs, designed for trust & safety operations.**

> This project demonstrates end-to-end ML engineering for security applications: from dataset analysis and model training, to calibrated inference, API deployment, and operational monitoring.

---

## Quick Start (Windows)

### Prerequisites
- Docker Desktop (running)
- WSL 2 (recommended)

### Running the System
To start both backend and frontend services:

**PowerShell**
```powershell
.\run.ps1
```

- **Backend:** http://localhost:8000
- **Frontend:** http://localhost:5173

### Testing the API
To run the integration tests against a running backend:

**PowerShell**
```powershell
.\test_api.ps1
```

---

## Problem Statement

Modern APIs (especially LLM APIs) face systematic abuse:
- **Prompt injection attacks** attempting to bypass safety controls
- **Automated policy violations** at scale
- **Coordinated campaigns** exploiting API endpoints

Manual review doesn't scale well to the amount of requests APIs get. 

This system uses ML to detect malicious content **before** it reaches downstream systems, with:
- **High recall** (catch violations) 
- **Calibrated probabilities** (reliable confidence scores)
- **Production-ready deployment** (real-time + batch processing)

---

## Dataset & Scope

- **Source:** [Benign-Malicious Prompt Classification](https://huggingface.co/datasets/guychuk/benign-malicious-prompt-classification) (464,470 entries)
- **Classes:** Balanced (50.7% malicious, 49.3% benign)
- **Split:** 70% train / 15% validation / 15% test
- **Domain:** General adversarial prompts (jailbreaks, policy evasion, harmful instructions)

**Why this dataset:**
- Large enough to train robust classifiers
- Publicly available (reproducible)
- Due to data classification concerns, I am not able to demonstrate here the exact dataset used in deployment.

---

## System Architecture

```
┌─────────────────┐
│   Input Text    │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────┐
│  TF-IDF Vectorizer          │
│  (20k features, 1-2 grams)  │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  Logistic Regression        │
│  (C=10, lbfgs solver)       │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  Probability Calibration    │
│  (Isotonic calibration)      │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  Threshold Decision         │
│  (0.45 - optimized F1)      │
└────────┬────────────────────┘
         │
         ▼
   BENIGN / MALICIOUS
```

**Architecture decisions:**
1. **TF-IDF over embeddings**: Faster inference, interpretable features, sufficient for this task
2. **Logistic regression**: Baseline with excellent speed/accuracy trade-off
3. **Calibration**: Ensures probabilities are reliable for threshold-based decisions for monitoring centre
4. **0.45 threshold**: Selected via validation set PR-curve analysis (F1 optimization)

---

## Deployment Story

```
┌──────────────┐       ┌─────────────────┐       ┌────────────────────┐
│  Web Client  │──────▶│  NGINX Gateway  │──────▶│  FastAPI Backend    │
└──────────────┘       │  TLS + Routing  │       │  /v1/predict /v1/batch │
                       └────────┬────────┘       │  /health /metrics     │
                                │                └─────────┬──────────┘
                                │                          │
                                ▼                          ▼
                       ┌────────────────┐         ┌────────────────────┐
                       │ React UI       │         │ Model Artifacts     │
                       │ Static Assets  │         │ .pkl + config       │
                       └────────────────┘         └────────────────────┘
```

**Example NGINX reverse proxy (single host):**
```nginx
server {
  listen 80;
  server_name _;

  location /api/ {
    proxy_pass http://backend:8000/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
  }

  location / {
    root /usr/share/nginx/html;
    try_files $uri /index.html;
  }
}
```

**Production env example:** see [.env.production.example](file:///c:/Users/Admin/Desktop/Projects/malicious-content-detection-system/.env.production.example)

---

## Features

### 1. Real-Time Prediction API
```bash
curl -X POST "http://localhost:8000/v1/predict" \
  -H "Content-Type: application/json" \
  -d '{"texts": ["Hello world", "I want to kill someone"]}'
```

**Response:**
```json
{
  "predictions": [
    {
      "text": "Hello world",
      "label": "BENIGN",
      "probability_malicious": 0.023,
      "threshold": 0.45,
      "risk_level": "LOW",
      "recommended_action": "ALLOW"
    },
    {
      "text": "I want to kill someone",
      "label": "MALICIOUS",
      "probability_malicious": 0.98,
      "threshold": 0.45,
      "risk_level": "HIGH",
      "recommended_action": "BLOCK"
    }
  ]
}
```

### 2. Batch Processing
Upload CSV files for bulk scoring (optimized with joblib parallelization).

### 3. Model Info Endpoint
```bash
curl http://localhost:8000/model-info
```

### 4. FastUI & React Frontend
- **FastUI (Backend-driven):** http://localhost:8000/fastui
- **React Console:** http://localhost:5173

### 5. Observability (Quick)
- **Metrics (Prometheus):** curl http://localhost:8000/metrics/prometheus
- **Health:** curl http://localhost:8000/health (includes service_degraded)
- **Logging:** JSON logs with correlation IDs

---

##### Development

### Linting
**PowerShell**
```powershell
.\lint.ps1
```

**WSL / Bash**
```bash
./lint.sh
```

### Backend
```bash
pip install -r requirements-dev.txt
uvicorn api.app:app --reload
```
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Docker
```bash
docker compose up --build
```
