# Deployment Guide

Covers local, Docker, cloud, and Kubernetes deployment patterns.

## Prerequisites

- Python 3.11+
- Docker (for containerized deployment)
- 2GB RAM minimum
- Model artifacts in `models/` (`.pkl` files)

---

## Local

```bash
git clone https://github.com/junwenleong/malicious-content-detection-system.git
cd malicious-content-detection-system

python3.11 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
cp .env.development.example .env
python validate_env.py
```

Verify model files exist:

```bash
ls -lh models/
# malicious_content_detector_calibrated.pkl (~150MB)
# malicious_content_detector_config.pkl (~1KB)
```

If missing, train via the notebook: `jupyter notebook notebooks/malicious_content_detection_analysis.ipynb`

Start the server:

```bash
# Development (auto-reload)
uvicorn api.app:app --reload --port 8000

# Production
gunicorn api.app:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120
```

Validate:

```bash
curl http://localhost:8000/health
curl -X POST http://localhost:8000/v1/predict \
  -H "Content-Type: application/json" \
  -H "x-api-key: dev-secret-key-123" \
  -d '{"texts": ["Test message"]}'
```

---

## Docker

```bash
# Build
docker build -t malicious-content-detector:latest .

# Run
docker run -d --name malicious-detector -p 8000:8000 malicious-content-detector:latest

# Logs
docker logs -f malicious-detector

# Stop
docker stop malicious-detector && docker rm malicious-detector
```

Or use Docker Compose for both backend and frontend:

```bash
docker compose up --build          # Development
docker compose -f docker-compose.prod.yml up -d  # Production (hardened)
```

---

## Cloud

### AWS (EC2 + ALB)

1. Launch a `t3.medium` (2 vCPU, 4GB) with Ubuntu 22.04
2. Install Docker, pull the image, run on port 8000
3. Create an ALB target group pointing to HTTP:8000 with `/health` as the health check

### GCP (Cloud Run)

```bash
gcloud builds submit --tag gcr.io/PROJECT_ID/malicious-detector
gcloud run deploy malicious-detector \
  --image gcr.io/PROJECT_ID/malicious-detector \
  --platform managed --region us-central1 \
  --memory 2Gi --cpu 2
```

### Azure (Container Instances)

```bash
az acr build --registry myregistry --image malicious-detector:latest .
az container create \
  --resource-group myResourceGroup \
  --name malicious-detector \
  --image myregistry.azurecr.io/malicious-detector:latest \
  --cpu 2 --memory 4 --ports 8000
```

---

## Kubernetes

Deployment manifest:

```yaml
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
            requests: { memory: "2Gi", cpu: "1000m" }
            limits: { memory: "4Gi", cpu: "2000m" }
          livenessProbe:
            httpGet: { path: /health, port: 8000 }
            initialDelaySeconds: 10
            periodSeconds: 30
          readinessProbe:
            httpGet: { path: /health, port: 8000 }
            initialDelaySeconds: 5
            periodSeconds: 10
```

Service:

```yaml
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

```bash
kubectl apply -f k8s/
kubectl get pods
kubectl logs -l app=malicious-detector --tail=100 -f
```

---

## Performance Tuning

| Workload             | CPU     | Memory | Workers |
| -------------------- | ------- | ------ | ------- |
| Light (<10 req/s)    | 1 core  | 2GB    | 1-2     |
| Medium (10-50 req/s) | 2 cores | 4GB    | 2-4     |
| Heavy (50-200 req/s) | 4 cores | 8GB    | 4-8     |

Gunicorn auto-configures workers as `(2 × CPU cores) + 1` via `entrypoint.sh`.

---

## Security Checklist

- API key auth enforced on all prediction endpoints
- HMAC signing available for high-security deployments (`HMAC_ENABLED=true`)
- Brute-force protection: 5 failed auth attempts/min blocks the IP
- Input limits: 10k chars per text, 1000 items per batch, 10MB CSV max
- TLS termination at the load balancer (ALB, NGINX, Cloudflare)
- Non-root user in Docker containers
- Model integrity verified via SHA256 at startup

---

## Model Updates (Zero-Downtime)

**Blue/green:** Deploy the new version on a separate port, switch the load balancer, monitor, then decommission the old one.

**Rolling update (Kubernetes):**

```bash
kubectl set image deployment/malicious-detector api=malicious-content-detector:v2
```

Kubernetes handles the rollout automatically with the readiness probe gating traffic.

---

## Backup

```bash
# Model artifacts to S3
aws s3 sync models/ s3://your-bucket/models/backups/$(date +%Y%m%d)/

# Config is in version control (git tags)
```

---

## Troubleshooting

**Model files not found:** Run `git lfs install && git lfs pull`, or retrain via the notebook.

**Out of memory:** Increase container memory (`docker run -m 4g ...`) or reduce batch size.

**Rate limit exceeded:** Adjust `RATE_LIMIT_MAX` and `RATE_LIMIT_WINDOW` in your `.env`.
