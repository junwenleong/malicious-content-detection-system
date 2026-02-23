# Project Structure

## Directory Layout

```
malicious-content-detection-system/
├── api/                          # FastAPI app entry point
│   └── app.py                    # Main application setup
│
├── src/                          # Core application code
│   ├── api/                      # API layer
│   │   ├── auth.py              # Authentication & HMAC verification
│   │   ├── middleware.py        # Security, audit, Prometheus middleware
│   │   ├── schemas.py           # Pydantic request/response models
│   │   └── routes/              # API endpoint handlers
│   │       ├── predict.py       # Real-time prediction endpoint
│   │       ├── batch.py         # Batch processing endpoint
│   │       ├── health.py        # Health & model-info endpoints
│   │       └── metrics.py       # Prometheus metrics endpoint
│   │
│   ├── inference/               # ML inference layer
│   │   ├── base.py             # Base predictor interface
│   │   └── predictor.py        # Model loading, prediction, caching
│   │
│   ├── utils/                   # Utility modules
│   │   ├── circuit_breaker.py  # Resilience pattern
│   │   ├── rate_limiter.py     # Rate limiting
│   │   ├── metrics.py          # Prometheus metrics collection
│   │   └── policy.py           # Risk level & action decisions
│   │
│   ├── models/                  # Data models (if needed)
│   ├── features/                # Feature engineering (if needed)
│   ├── config.py               # Settings & environment config
│   └── __init__.py
│
├── frontend/                     # React TypeScript frontend
│   ├── src/
│   │   ├── components/          # React components
│   │   │   ├── Header.tsx
│   │   │   ├── ConnectionPanel.tsx
│   │   │   ├── AnalyzeTab.tsx
│   │   │   └── BatchTab.tsx
│   │   ├── App.tsx              # Main app component
│   │   ├── main.tsx             # Entry point
│   │   ├── types.ts             # TypeScript type definitions
│   │   └── index.css            # Global styles
│   ├── public/                  # Static assets
│   ├── package.json             # Frontend dependencies
│   ├── vite.config.ts           # Vite build configuration
│   ├── tsconfig.json            # TypeScript configuration
│   ├── eslint.config.js         # ESLint rules
│   └── Dockerfile               # Frontend container image
│
├── tests/                        # Test suite
│   ├── test_api.py              # API integration tests
│   ├── test_basic.py            # Basic functionality tests
│   ├── test_circuit_breaker.py  # Circuit breaker tests
│   ├── test_rate_limiter.py     # Rate limiter tests
│   ├── test_error_handling.py    # Error handling tests
│   ├── test_hmac.py             # HMAC signature tests
│   ├── test_mocked_predict.py    # Mocked prediction tests
│   ├── test_ai_audit.py         # AI behavior audit tests
│   ├── test_logic_audit.py      # Logic audit tests
│   └── perf_check.py            # Performance benchmarks
│
├── models/                       # ML model artifacts
│   ├── malicious_content_detector_calibrated.pkl
│   └── malicious_content_detector_config.pkl
│
├── data/                         # Data directories
│   ├── raw/                     # Raw input data
│   └── processed/               # Processed/cached data
│
├── notebooks/                    # Jupyter notebooks for analysis
│   └── malicious_content_detection_analysis.ipynb
│
├── docs/                         # Documentation
│   ├── DEPLOYMENT.md            # Deployment guide
│   ├── SCALING_STRATEGY.md      # Scaling considerations
│   └── adr/                     # Architecture Decision Records
│       └── 003-security-hardening.md
│
├── .kiro/                        # Kiro configuration
│   └── steering/                # Steering documents (this folder)
│
├── Dockerfile                    # Backend container image
├── docker-compose.yml            # Development compose file
├── docker-compose.prod.yml       # Production compose file
├── entrypoint.sh                 # Container entrypoint script
│
├── .env.development.example      # Example development config
├── .env.production.example       # Example production config
├── requirements.txt              # Python dependencies (meta)
├── requirements-api.txt          # API runtime dependencies
├── requirements-dev.txt          # Development dependencies
│
├── README.md                     # Project overview
├── MODEL_CARD.md                 # Model documentation
├── DEPLOYMENT.md                 # Deployment guide
├── LICENSE                       # License file
├── .gitignore                    # Git ignore rules
└── validate_env.py               # Environment validation script
```

## Key Architectural Layers

### 1. API Layer (`src/api/`)
- **Routes**: Endpoint handlers for `/v1/predict`, `/v1/batch`, `/health`, `/metrics`
- **Middleware**: Security headers, audit logging, Prometheus metrics, CORS
- **Auth**: API key validation, HMAC signature verification
- **Schemas**: Pydantic models for request/response validation

### 2. Inference Layer (`src/inference/`)
- **Predictor**: Loads model, handles predictions, manages LRU cache
- **Base**: Interface for extensibility

### 3. Utilities (`src/utils/`)
- **Circuit Breaker**: Protects against cascading failures
- **Rate Limiter**: Prevents abuse and brute-force attacks
- **Metrics**: Prometheus metric collection
- **Policy**: Risk level determination and action recommendations

### 4. Configuration (`src/config.py`)
- Centralized settings management via Pydantic
- Environment-driven configuration
- Security validation (API key complexity, HMAC secret length)

### 5. Frontend (`frontend/`)
- React + TypeScript for type safety
- Material-UI for consistent design
- Tabs for Analyze (single) and Batch (CSV upload) workflows
- Connection panel for API authentication

## Data Flow

```
User Input (Text/CSV)
    ↓
Frontend (React) or API Client
    ↓
FastAPI Endpoint (/v1/predict or /v1/batch)
    ↓
Authentication & Rate Limiting
    ↓
Input Validation & Sanitization (Unicode NFKC)
    ↓
Predictor (with LRU Cache)
    ↓
TF-IDF Vectorizer + Logistic Regression
    ↓
Probability Calibration
    ↓
Risk Level & Action Decision (Policy)
    ↓
Response (JSON with predictions, risk levels, actions)
    ↓
Audit Logging & Metrics
```

## Testing Organization

- **Unit Tests**: Individual component testing (rate limiter, circuit breaker, auth)
- **Integration Tests**: Full API flow testing
- **Performance Tests**: Latency and throughput benchmarks
- **Audit Tests**: AI behavior, logic, and security audits

## Configuration & Secrets

- **Environment Variables**: Loaded via `pydantic-settings`
- **Secrets**: API keys, HMAC secrets (never hardcoded in production)
- **Model Integrity**: SHA256 checksums verified at startup
- **Validation**: `validate_env.py` ensures required config is present

## Deployment Artifacts

- **Backend Image**: Multi-stage Dockerfile, non-root user, minimal attack surface
- **Frontend Image**: Nginx-based static serving with build-time API URL injection
- **Compose Files**: Development (permissive) and production (hardened) variants
