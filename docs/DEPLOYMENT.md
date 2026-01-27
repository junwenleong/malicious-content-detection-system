# Deployment

## Overview

This document covers production deployment patterns for the system.

**Deployment targets:**
- Local development (testing)
- Docker container (portable deployment)
- Cloud platforms (AWS/GCP/Azure)
- Kubernetes (scalable production) with EKS in mind

---

## Prerequisites

- Python 3.11+
- Docker (optional, for containerisation)
- 2GB RAM minimum for model processing
- Model artifacts (`.pkl` files)

---

## Local Deployment

### 1. Environment Setup

```bash
# Clone repository
git clone https://github.com/junwenleong/malicious-content-detection-system.git
cd malicious-content-detection-system

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Verify Model Artifacts

```bash
ls -lh models/
# Should show:
# malicious_content_detector_calibrated.pkl (~150MB)
# malicious_content_detector_config.pkl (~1KB)
```

If missing, train the model:
```bash
jupyter notebook notebooks/malicious_content_detection_analysis.ipynb
# Run all cells
```

### 3. Start API Server

```bash
uvicorn api.app:app --host 0.0.0.0 --port 8000 --workers 1
```

**Development mode** (auto-reload):
```bash
uvicorn api.app:app --reload --port 8000
```

### 4. Validate Deployment

```bash
# Health check
curl http://localhost:8000/health

# Expected:
# {"status": "healthy", "model_loaded": true, "timestamp": "2025-01-..."}

# Test prediction
curl -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{"texts": ["Test message"]}'
```

---

## Docker Deployment

### 1. Build Image

```bash
docker build -t malicious-content-detector:latest .
```

### 2. Run Container

```bash
docker run -d \
  --name malicious-detector \
  -p 8000:8000 \
  malicious-content-detector:latest
```

### 3. View Logs

```bash
docker logs -f malicious-detector
```

### 4. Stop Container

```bash
docker stop malicious-detector
docker rm malicious-detector
```

---

## Cloud Deployment

### AWS (EC2 + Application Load Balancer)

#### 1. Launch EC2 Instance

```bash
# Ubuntu 22.04 LTS
# t3.medium (2 vCPU, 4GB RAM) minimum
# Security group: Allow inbound 8000, 22
```

#### 2. Setup on EC2

```bash
ssh -i your-key.pem ubuntu@<ec2-public-ip>

# Install Docker
sudo apt update
sudo apt install -y docker.io
sudo systemctl start docker
sudo usermod -aG docker ubuntu

# Pull and run container
docker pull ghcr.io/junwenleong/malicious-content-detector:latest
docker run -d -p 8000:8000 malicious-content-detector:latest
```

#### 3. Configure ALB

```bash
# Target group: HTTP:8000
# Health check: GET /health
# Healthy threshold: 2
# Unhealthy threshold: 3
# Interval: 30s
```

### GCP (Cloud Run)

```bash
# Build and push to GCR
gcloud builds submit --tag gcr.io/PROJECT_ID/malicious-detector

# Deploy to Cloud Run
gcloud run deploy malicious-detector \
  --image gcr.io/PROJECT_ID/malicious-detector \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2
```

### Azure (Container Instances)

```bash
# Push to ACR
az acr build --registry myregistry \
  --image malicious-detector:latest .

# Deploy to ACI
az container create \
  --resource-group myResourceGroup \
  --name malicious-detector \
  --image myregistry.azurecr.io/malicious-detector:latest \
  --cpu 2 \
  --memory 4 \
  --ports 8000
```

---

## Kubernetes Deployment

### 1. Deployment Manifest

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: malicious-detector
spec:
  replicas: 3
  selector:
    matchLabels:
      app: malicious-detector
  template:
    metadata:
      labels:
        app: malicious-detector
    spec:
      containers:
      - name: api
        image: malicious-content-detector:latest
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
```

### 2. Service Manifest

```yaml
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: malicious-detector-service
spec:
  selector:
    app: malicious-detector
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

### 3. Deploy

```bash
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml

# Check status
kubectl get pods
kubectl get svc

# View logs
kubectl logs -l app=malicious-detector --tail=100 -f
```

---

## Performance Tuning

### Concurrency Settings

**Single-worker** (default):
```bash
uvicorn api.app:app --workers 1
```

**Multi-worker** (CPU-bound tasks):
```bash
uvicorn api.app:app --workers 4
```

**With Gunicorn** (production):
```bash
gunicorn api.app:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile -
```

### Resource Allocation

| Workload | CPU | Memory | Workers |
|----------|-----|--------|---------|
| Light (<10 req/s) | 1 core | 2GB | 1-2 |
| Medium (10-50 req/s) | 2 cores | 4GB | 2-4 |
| Heavy (50-200 req/s) | 4 cores | 8GB | 4-8 |

---

## Monitoring & Observability

### Built-in Metrics

```bash
curl http://localhost:8000/metrics
```

Returns:
- `uptime_seconds`
- `total_requests`
- `total_predictions`
- `predictions_by_class`
- `average_latency_ms`
- `errors`
- `requests_per_second`

### Prometheus Integration (TODO)

Export metrics in Prometheus format:
```python
# Add prometheus_client dependency
from prometheus_client import Counter, Histogram, generate_latest

# Instrument endpoints
# Expose /metrics endpoint
```

### Logging

Structured JSON logging:
```bash
# Configure in app.py
logging.basicConfig(
    level=logging.INFO,
    format='{"time":"%(asctime)s","name":"%(name)s","level":"%(levelname)s","message":"%(message)s"}'
)
```

Aggregate with:
- **CloudWatch Logs** (AWS)
- **Cloud Logging** (GCP)
- **Azure Monitor** (Azure)
- **ELK Stack** (self-hosted)

---

## Security Considerations

### 1. Rate Limiting

Current implementation (in-memory):
```python
# api/app.py
rate_limiter = RateLimiter(max_requests=100, window_seconds=60)
```

**Production alternative:**
- Redis-based distributed rate limiting
- API Gateway rate limiting (AWS API Gateway, GCP API Gateway)

### 2. Input Validation

- Max text length: 10,000 characters
- Max batch size: 100 texts per request
- File size limit: 10MB (CSV uploads)

### 3. Authentication (TODO)

Add API key authentication:
```python
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key")

@app.post("/predict")
async def predict(request: PredictRequest, api_key: str = Depends(api_key_header)):
    if api_key not in VALID_API_KEYS:
        raise HTTPException(status_code=403, detail="Invalid API key")
    # ... existing logic
```

### 4. HTTPS/TLS

**Development:**
```bash
uvicorn api.app:app --ssl-keyfile=./key.pem --ssl-certfile=./cert.pem
```

**Production:**
- Use ALB/Load Balancer for TLS termination
- Let's Encrypt for free certificates
- Cloudflare for CDN + DDoS protection

---

## Operational Runbook

### Common Issues

#### 1. Model Files Not Found

**Error:**
```
FileNotFoundError: Model files not found. Train the model first.
```

**Fix:**
```bash
# Ensure Git LFS is installed
git lfs install
git lfs pull

# Or retrain:
jupyter notebook notebooks/malicious_content_detection_analysis.ipynb
```

#### 2. Out of Memory

**Error:**
```
MemoryError: Unable to allocate array
```

**Fix:**
```bash
# Increase container memory
docker run -m 4g -p 8000:8000 malicious-content-detector

# Or reduce batch size in code
```

#### 3. Rate Limit Exceeded

**Error:**
```
429 Rate limit exceeded
```

**Fix:**
```bash
# Adjust rate limiter config in api/app.py
rate_limiter = RateLimiter(max_requests=500, window_seconds=60)
```

---

## Updating the Model

### Zero-Downtime Updates

**Strategy 1: Blue/Green Deployment**
```bash
# Deploy new version with different tag
docker run -d -p 8001:8000 malicious-detector:v2

# Switch load balancer to :8001
# Monitor for errors
# Decommission :8000
```

**Strategy 2: Rolling Update (Kubernetes)**
```bash
# Update image in deployment.yaml
kubectl set image deployment/malicious-detector \
  api=malicious-content-detector:v2

# Kubernetes handles rolling update automatically
```

### Model Versioning

Store models in versioned directory:
```
models/
├── v1.0/
│   ├── malicious_content_detector_calibrated.pkl
│   └── malicious_content_detector_config.pkl
├── v1.1/
│   ├── malicious_content_detector_calibrated.pkl
│   └── malicious_content_detector_config.pkl
```

Load specific version:
```python
MODEL_VERSION = os.getenv("MODEL_VERSION", "v1.0")
MODEL_PATH = f"models/{MODEL_VERSION}/malicious_content_detector_calibrated.pkl"
```

---

## Cost Estimation (sample;dummy)

### AWS (us-east-1) 

| Component | Type | Cost/month |
|-----------|------|------------|
| EC2 | t3.medium | ~$30 |
| ALB | Standard | ~$20 |
| Data transfer | 1TB | ~$90 |
| **Total** | | **~$140/month** |

---

## Backup & Disaster Recovery

### Model Artifacts
```bash
# Backup to S3
aws s3 sync models/ s3://my-bucket/models/backups/$(date +%Y%m%d)/

# Restore
aws s3 sync s3://my-bucket/models/backups/20250127/ models/
```

### Configuration
```bash
# Version control (already in Git)
git tag v1.0.0
git push origin v1.0.0
```


```