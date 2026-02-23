# Technology Stack & Build System

## Backend Stack

**Language**: Python 3.x
**Framework**: FastAPI 0.128.0
**Server**: Uvicorn (development) / Gunicorn (production)

### Key Dependencies
- **ML/Data**: scikit-learn 1.8.0, joblib 1.5.3, numpy 1.26.0+
- **API**: FastAPI 0.128.0, pydantic 2.12.5, python-multipart 0.0.21
- **Observability**: prometheus-client 0.19.0
- **Config**: pydantic-settings 2.0.0+

### Development Dependencies
- **Testing**: pytest 8.0.0+, pytest-cov 4.1.0+
- **Linting**: ruff 0.3.0+, mypy 1.8.0+, black 24.0.0+
- **Analysis**: jupyter, pandas, matplotlib, seaborn

## Frontend Stack

**Language**: TypeScript 5.9.3
**Framework**: React 19.2.0
**Build Tool**: Vite 7.3.1
**UI Library**: Material-UI (MUI) 7.3.4
**Styling**: Emotion (React CSS-in-JS)

### Development Tools
- **Linting**: ESLint 9.39.1 with TypeScript support
- **Type Checking**: TypeScript compiler

## Containerization

- **Backend**: Multi-stage Dockerfile with non-root user
- **Frontend**: Nginx-based static serving
- **Orchestration**: Docker Compose (development & production variants)

## Common Commands

### Backend Development
```bash
# Install dependencies
pip install -r requirements-dev.txt

# Run development server (with auto-reload)
uvicorn api.app:app --reload

# Run tests
pytest tests/

# Run tests with coverage
pytest --cov=src tests/

# Linting & formatting
ruff check src/
mypy src/
black src/
```

### Frontend Development
```bash
# Install dependencies
cd frontend && npm install

# Run development server
npm run dev

# Build for production
npm run build

# Linting
npm run lint

# Preview production build
npm run preview
```

### Docker
```bash
# Build and run both services
docker compose up --build

# Production deployment
docker compose -f docker-compose.prod.yml up -d

# View logs
docker compose logs -f backend
docker compose logs -f frontend
```

### Testing & Validation
```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_api.py

# Run with verbose output
pytest -v tests/

# Run linting checks
./lint.sh  # macOS/Linux
.\lint.ps1 # Windows PowerShell

# Validate environment configuration
python validate_env.py
```

### API Testing
```bash
# Windows PowerShell
.\test_api.ps1

# macOS/Linux
pytest tests/test_api.py
```

## Environment Configuration

- **Backend**: `.env` file (copy from `.env.development.example` or `.env.production.example`)
- **Frontend**: `frontend/.env` file (copy from `frontend/.env.development.example`)
- **Validation**: Run `python validate_env.py` to verify configuration

## Key Configuration Variables

**Backend** (`.env`):
- `API_KEY`: Authentication key for API endpoints
- `HMAC_ENABLED`: Enable HMAC signature verification
- `HMAC_SECRET`: Secret for HMAC signing (min 32 chars)
- `RATE_LIMIT_MAX`: Max requests per window
- `RATE_LIMIT_WINDOW`: Rate limit window in seconds
- `BREAKER_ENABLED`: Enable circuit breaker
- `ALLOWED_ORIGINS`: CORS allowed origins (JSON array)

**Frontend** (`.env`):
- `VITE_API_URL`: Backend API URL (e.g., `http://localhost:8000`)

## Model Files

Located in `models/`:
- `malicious_content_detector_calibrated.pkl`: Trained model artifact
- `malicious_content_detector_config.pkl`: Model configuration

Model integrity is verified via SHA256 checksums at startup.

## Performance Characteristics

- **Single prediction latency**: ~4ms (p50)
- **Batch processing**: Parallelized with joblib
- **Concurrency**: Gunicorn auto-configures workers as `(2 x CPU cores) + 1`
- **Caching**: LRU cache (10,000 items) for repeated queries
