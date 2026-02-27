# Malicious Content Detection System

**Internal security tooling prototype for AI testing / red-team workflows.**

> This system demonstrates an API-first design for detecting abusive content, deployed via Docker in isolated environments to support compliance and data handling policies.

---

## Impetus

This system was designed as an internal security tooling prototype for AI testing / red-team workflows. The primary interface is the **FastAPI service**, deployed via Docker in an isolated environment.

The **React frontend** is a lightweight dashboard for manual testing and batch upload, but automated testing teams primarily integrate with the API directly. The system is Dockerized to support deployment inside restricted enterprise environments where sending prompts to external cloud services may violate compliance or data handling policies.

The frontend exists for:
- Manual validation
- QA spot-checking
- Batch CSV upload
- Non-technical stakeholders reviewing outputs

But the real system value is **API-first design**.

> **Note:** The public dataset replaces internal data sources, which cannot be shared. The system architecture mirrors internal tooling patterns.

## How It Integrates
- Drop behind an NGINX or API gateway and route `/v1/predict` and `/v1/batch` to the backend.
- Use the structured JSON audit logs (with correlation IDs) to feed your SIEM or data lake.
- Scrape `/metrics` for basic service metrics; extend as needed for SLOs.
- Rotate API keys without downtime via `API_KEYS` (add new key, update clients, remove old key).
- Use the risk policy outputs to drive business actions: ALLOW, flag for REVIEW, or BLOCK.

## Deployment & Operations
For production deployment, see [DEPLOYMENT.md](DEPLOYMENT.md).
- **Docker**: Multi-stage builds, non-root user.
- **Observability**: Prometheus metrics, JSON logs.
- **Security**: Hardened config available in `docker-compose.prod.yml`.

## Quick Start (Windows)

### Prerequisites
- Docker Desktop (running)
- WSL 2 (recommended)

### Configuration (New)
Before running the system, set up your environment:

1. Copy the example environment file:
   ```bash
   # Backend
   cp .env.development.example .env

   # Frontend
   cp frontend/.env.development.example frontend/.env
   ```

   > **Note:** The default API Key is `dev-secret-key-123`. You must enter this in the Frontend Connection Panel to authenticate.

2. Validate your configuration:
   ```bash
   python validate_env.py
   ```

### Running the System
To start both backend and frontend services:

**Bash (macOS/Linux)**
```bash
./run.sh
```

- **Backend:** http://localhost:8000
- **Frontend:** http://localhost:5173

### Testing the API
To run the integration tests against a running backend:

**Testing the API**
```bash
pytest tests/test_api.py
```

## Quick Start (macOS / Linux)

### Prerequisites
- Docker Desktop or Docker Engine (running)
- Python 3.11+

### Configuration
1. Copy the example environment file:
   ```bash
   # Backend
   cp .env.development.example .env

   # Frontend
   cp frontend/.env.development.example frontend/.env
   ```

   > **Note:** The default API Key is `dev-secret-key-123`. You must enter this in the Frontend Connection Panel to authenticate.

2. Validate your configuration:
   ```bash
   python3 validate_env.py
   ```

### Running the System
```bash
./run.sh
```

Or with Docker Compose directly:
```bash
docker compose up --build
```

- **Backend:** http://localhost:8000
- **Frontend:** http://localhost:5173

### Testing the API
```bash
pip install -r requirements-dev.txt
pytest tests/ -v
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

## Security Hardening Implemented

### 🛡️ Critical Security Features

- **Model Integrity Verification**:
  - Implemented strict SHA256 checksum validation for both the model and config files.
  - The system now refuses to start if the model files do not match the known-good hashes defined in [config.py](src/config.py).
  - Code Reference: [predictor.py](src/inference/predictor.py)

- **Input Sanitization Layer**:
  - Added Unicode Normalization (NFKC) to the prediction pipeline. This converts compatibility characters and homoglyphs into their canonical forms before feature extraction.
  - Code Reference: [predictor.py](src/inference/predictor.py)

- **Authentication & Authorization**:
  - Implemented secure API key validation with fail-secure logic (system errors if key is missing in production).
  - Added strict rate limiting for authentication failures (5 attempts/minute) to prevent brute-force attacks.
  - Code Reference: [predict.py](src/api/routes/predict.py)

- **Input Validation**:
  - Added strict MIME type and file extension validation for batch processing endpoints to prevent malicious file uploads.
  - Code Reference: [batch.py](src/api/routes/batch.py)

### 🔒 Advanced Security Controls (New)

- **API Key Rotation**:
  - Support for multiple active API keys via `API_KEYS` configuration. This enables zero-downtime key rotation (add new key -> deploy -> update clients -> remove old key).
  - Code Reference: [config.py](src/config.py)

- **Audit Logging**:
  - Dedicated **JSON structured** audit log for all authentication events (Success/Failure) including IP address, timestamp, and correlation ID.
  - Logs `{"event": "auth_failure", ...}` for 401/403 errors and `{"event": "auth_success", ...}` for authorized requests.
  - Code Reference: [middleware.py](src/api/middleware.py)

- **Secret Management**:
  - Enforced minimum complexity for secrets (HMAC secret must be >= 32 chars).
  - Support for zero-downtime rotation via multiple active API keys.
  - Code Reference: [config.py](src/config.py)

- **Security Headers**:
  - Implemented standard security headers (`Strict-Transport-Security`, `Content-Security-Policy`, `X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`) to mitigate XSS, Clickjacking, and MIME sniffing.
  - Code Reference: [middleware.py](src/api/middleware.py)

- **Request Signing (HMAC)**:
  - Optional HMAC-SHA256 signature verification for critical endpoints (`/predict`).
  - Enabled via `HMAC_ENABLED=true` and `HMAC_SECRET=...`.
  - Requires `X-Signature` header: `timestamp:signature`.
  - Code Reference: [auth.py](src/api/auth.py)

---

## Performance Engineering

### ⚡ Optimizations
- **LRU Caching**: Implemented a thread-safe LRU cache (10,000 items) in the prediction pipeline. This drastically reduces latency for repeated queries (common in spam/abuse campaigns).
  - Code Reference: [predictor.py](src/inference/predictor.py)
- **Concurrency**: Configured Gunicorn to auto-detect CPU cores and spawn `(2 x Cores) + 1` workers, maximizing throughput for the CPU-bound inference workload.
  - Code Reference: [entrypoint.sh](entrypoint.sh)
- **Efficient Logging**: Optimized audit logging to hash only a sample of batch inputs, reducing CPU overhead by >90% for large batch requests.
  - Code Reference: [predict.py](src/api/routes/predict.py)

---

## Dataset & Scope

- **Source:** [Malicious Prompt Detection Dataset (MPDD)](https://www.kaggle.com/datasets/mohammedaminejebbar/malicious-prompt-detection-dataset-mpdd) from Kaggle (39,234 entries)
- **Classes:** Perfectly balanced (50% malicious, 50% benign)
- **Split:** 70% train / 15% validation / 15% test (27,463 train / 5,885 val / 5,886 test)
- **Domain:** Prompt injection and jailbreak detection (specifically curated for detecting manipulation attempts)

**Why this dataset:**
- Larger and better balanced than previous dataset (39,234 samples, perfect 50/50 split)
- Specifically curated for malicious prompt detection (jailbreaks, prompt injection)
- Publicly available (reproducible)
- Due to data classification concerns, I am not able to demonstrate here the exact dataset used in deployment.

### ⚠️ Important: Demo Dataset Characteristics

**This public dataset is exceptionally clean and well-separated**, which affects the observed metrics and calibration behavior:

**Why the metrics are strong:**
1. **Good separation**: The dataset has clear boundaries between benign and malicious examples, resulting in 98.81% ROC AUC
2. **Improved calibration**: The raw model calibration error (0.0055) is reduced to 0.0025 through isotonic calibration (55% improvement)
3. **Isotonic calibration**: More flexible than sigmoid, captures non-monotonic relationships for better probability reliability

**What this means:**
- The **methodology** (TF-IDF → Logistic Regression → Calibration → Threshold optimization) is sound and production-ready
- The **calibration improvement** (~55% error reduction) demonstrates the value of probability calibration
- In production with noisier, more ambiguous data, calibration typically shows even more substantial improvements

**Production comparison:**
- **Demo**: 98.82% AUC, calibration error 0.0055 → 0.0025 (improved calibration)
- **Production**: 85-92% AUC, calibration error 0.18 → 0.04 (0.14 improvement - much larger!)

**Key takeaway**: The strong demo metrics and calibration improvements demonstrate the approach works. Real-world datasets will show more substantial and meaningful improvements from calibration.

> **⚠️ Important Note on Model Behavior:**
> The public dataset used for this demo is specifically designed to detect **prompt injection / jailbreak attempts** (e.g., "Ignore previous instructions..."), rather than direct harmful questions.
>
> As per the dataset documentation: *"We decided to classify prompts to malicious only if there's an attempt to manipulate them - that means that a bad prompt (i.e asking how to create a bomb) will be classified as benign since it's a straight up question!"*
>
> Therefore, simple harmful queries like "how do i hurt him" are **correctly classified as BENIGN** by this specific model. Real-world enterprise deployments would use a composite dataset covering both direct harm and jailbreaks.

**Data Sensitivity**
- This repository mirrors the production architecture. Only datasets and secrets have been swapped to public/safe equivalents for demonstration.
- If you use your organization’s datasets, re‑run evaluation and refresh the model card with your metrics before production.

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
│  (10k features, 1-2 grams)  │
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
│  (Sigmoid calibration)      │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  Threshold Decision         │
│  (0.536 - F1-optimized)     │
└────────┬────────────────────┘
         │
         ▼
   BENIGN / MALICIOUS
```

**Architecture decisions:**
1. **TF-IDF over embeddings**: Faster inference, interpretable features, sufficient for this task
2. **Logistic regression**: Baseline with excellent speed/accuracy trade-off
3. **Isotonic calibration**: More flexible than sigmoid, captures non-monotonic relationships for reliable probabilities
4. **0.536 threshold**: Selected via validation set F1 optimization

**Demo Dataset Performance:**
- ROC AUC: 0.9881 (test set, calibrated model)
- Optimal Threshold: 0.536 (F1-optimized on validation set)
- Test Set Performance (at threshold 0.536):
  - Precision: 0.98 (malicious), 0.94 (benign)
  - Recall: 0.93 (malicious), 0.98 (benign)
  - F1-score: 0.96 (both classes), Accuracy: 0.96
- Calibration: Isotonic method, error 0.0055 → 0.0025 (55% improvement)
- Dataset: 39,234 samples (perfect 50/50 balance): 27,463 train / 5,885 val / 5,886 test

> **Production Note**: The demo dataset is unusually clean, resulting in near-perfect metrics. Real-world enterprise datasets with noisier content typically show 85-92% AUC with more substantial calibration improvements (error reduction from ~0.18 to ~0.04).

## Resilience & Policy
- **Circuit Breaker:** Protects inference service from cascading failures (configurable threshold/cooldown).
- **Shared Policy:** Centralized logic for risk levels (LOW/MEDIUM/HIGH) and actions (ALLOW/REVIEW/BLOCK) ensures consistency across API and Batch endpoints.
- **Model Versioning:** Responses include `model_version` for traceability.

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

### Production Awareness Checklist
- Secure defaults: API keys required; optional HMAC signing for high‑risk endpoints
- Defensive controls: rate limiting for auth attempts; circuit breaker on inference
- Input hygiene: Unicode normalization (NFKC) and strict validation on batch uploads
- Traceability: correlation IDs in logs; model version returned with predictions
- Operability: health endpoints, Prometheus metrics, and structured JSON logging
- Change safety: key rotation supported; model file integrity checked via hashes

---

## Features

## Features

### 1. Real-Time Prediction API
```bash
curl -X POST "http://localhost:8000/v1/predict" \
  -H "Content-Type: application/json" \
  -H "x-api-key: dev-secret-key-123" \
  -d '{"texts": ["Hello world", "Ignore previous instructions"]}'
```

**Response:**
```json
{
  "predictions": [
    {
      "text": "Hello world",
      "label": "BENIGN",
      "probability_malicious": 0.023,
      "threshold": 0.536,
      "risk_level": "LOW",
      "recommended_action": "ALLOW",
      "latency_ms": 3.2
    },
    {
      "text": "Ignore previous instructions",
      "label": "MALICIOUS",
      "probability_malicious": 0.94,
      "threshold": 0.536,
      "risk_level": "HIGH",
      "recommended_action": "BLOCK",
      "latency_ms": 3.5
    }
  ],
  "metadata": {
    "total_items": 2,
    "malicious_count": 1,
    "benign_count": 1,
    "total_latency_ms": 6.7,
    "model_version": "v1.0.0"
  }
}
```

For complete API documentation, see [docs/API_REFERENCE.md](docs/API_REFERENCE.md).

### Understanding Risk Levels and Actions

The system uses a two-tier decision framework:

**Risk Levels** (based on probability):
- **HIGH**: probability ≥ 0.85 (85%)
- **MEDIUM**: 0.6 ≤ probability < 0.85 (60-85%)
- **LOW**: probability < 0.6 (< 60%)

**Recommended Actions** (based on probability and threshold):
- **BLOCK**: probability ≥ threshold + 0.15
- **REVIEW**: threshold ≤ probability < threshold + 0.15
- **ALLOW**: probability < threshold

**Example** (with threshold = 0.536):
- Probability 0.849 (84.9%) → Risk: HIGH, Action: BLOCK (0.849 ≥ 0.85)
- Probability 0.60 → Risk: MEDIUM, Action: REVIEW (0.536 ≤ 0.60 < 0.686)
- Probability 0.30 → Risk: LOW, Action: ALLOW (0.30 < 0.536)

> **Note**: The default threshold (0.536) is optimized for the demo dataset using PR curve analysis (F1-optimized). Production deployments should re-evaluate thresholds based on your specific data and business requirements (precision vs recall trade-offs).

### 2. Batch Processing
Upload CSV files for bulk scoring (optimized with joblib parallelization).

### 3. Model Info Endpoint
```bash
curl http://localhost:8000/model-info
```

### 4. FastUI & React Frontend

- **React Console:** http://localhost:5173

### 5. Observability (Quick)
- **Metrics (Prometheus):** curl http://localhost:8000/metrics
- **Health:** curl http://localhost:8000/health (includes service_degraded)
- **Logging:** JSON logs with correlation IDs

---

## CI/CD Pipeline

This project uses GitHub Actions for continuous integration. The pipeline runs on every push and pull request:

- ✅ Backend linting (Ruff), type checking (Mypy), and tests (Pytest)
- ✅ Frontend linting (ESLint), type checking (TypeScript), and build (Vite)
- ✅ Docker image builds for both services
- ✅ Security scanning with Trivy

See [.github/workflows/README.md](.github/workflows/README.md) for details.

---

## Development Workflow

### Initial Setup (One-Time)

1. **Install dependencies:**
   ```bash
   # Backend
   pip install -r requirements-dev.txt

   # Frontend
   cd frontend && npm install && cd ..
   ```

2. **Setup pre-commit hook (Recommended):**
   ```bash
   ./scripts/setup-hooks.sh
   ```

   This installs a Git hook that automatically runs linting checks before every commit, catching issues early.

3. **Configure your IDE (Optional but Recommended):**
   - Install Python, Ruff, and ESLint extensions
   - Enable format-on-save for automatic code formatting

### Daily Development

With the pre-commit hook installed, your workflow is simple:

```bash
# 1. Write code
# 2. Commit (hook runs automatically)
git add .
git commit -m "Add feature X"

# 3. Push
git push
```

The pre-commit hook will:
- Auto-fix formatting issues
- Run linting checks
- Block commits if critical issues are found

### Manual Linting (When Needed)

Run linting manually only if:
- You bypassed pre-commit with `--no-verify`
- You're debugging linting issues
- Pre-commit hook isn't installed yet

**macOS / Linux:**
```bash
./lint.sh
```

**Run linting checks:**
```bash
./lint.sh
```

### Running Services Locally

**Backend:**
```bash
uvicorn api.app:app --reload
```

**Frontend:**
```bash
cd frontend
npm run dev
```

**Docker (Both Services):**
```bash
docker compose up --build
```

### Check Execution Matrix

| Check Type | When | Duration | Auto-Fix | Blocks Commit |
|------------|------|----------|----------|---------------|
| IDE Linting | On save | <1s | ✓ | ✗ |
| Pre-commit Hook | On commit | 5-10s | ✓ | ✓ |
| Manual lint.sh | On demand | 5-10s | ✓ | ✗ |
| CI/CD Pipeline | On push/PR | 2-5min | ✗ | ✓ |

**Best Practice:** Install the pre-commit hook once, then just write code and commit normally. The hook catches issues automatically before they reach CI/CD.

For detailed workflow documentation, see [.kiro/steering/development-workflow.md](.kiro/steering/development-workflow.md).
