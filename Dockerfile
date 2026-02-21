# Multi-stage build for smaller final image
FROM python:3.11-slim as builder

WORKDIR /app

# Install dependencies
COPY requirements-api.txt .
RUN pip install --no-cache-dir -r requirements-api.txt

# Final stage
FROM python:3.11-slim

WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /usr/local /usr/local

COPY api/ ./api/
COPY src/ ./src/
COPY models/ ./models/

# Ensure model files exist (fail-fast if missing)
RUN test -f models/malicious_content_detector_calibrated.pkl || \
    (echo "ERROR: Model file not found. Train the model first." && exit 1)

ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8000

RUN adduser --disabled-password --gecos "" appuser
USER appuser

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Run application
CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
