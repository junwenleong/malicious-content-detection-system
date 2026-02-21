# Deployment & Operations Audit

This document outlines the DevOps audit findings and provides a guide for production-grade deployment.

## 🛡️ DevOps Audit Report

### ✅ Strengths
- **Immutable Infrastructure**: The backend image includes all code and dependencies; no code is mounted at runtime in production.
- **Observability**: 
  - Structured JSON logging is enabled by default.
  - Prometheus metrics are exposed at `/metrics`.
  - Health checks are implemented at `/health`.
- **Security**:
  - Container runs as non-root user (`appuser`).
  - `PYTHONUNBUFFERED=1` ensures logs are flushed immediately.
  - Multi-stage builds reduce attack surface and image size.

### ⚠️ Risks & Remediations
| Risk | Severity | Remediation | Status |
|------|----------|-------------|--------|
| **Hardcoded Secrets** | High | `docker-compose.yml` contains default API keys. Use environment variables in production. | ✅ Fixed in `docker-compose.prod.yml` |
| **Unbounded Resources** | Medium | No CPU/Memory limits defined. Container could starve host. | ✅ Fixed in `docker-compose.prod.yml` |
| **Build Context Bloat** | Low | `frontend/` and `tests/` were included in backend build context. | ✅ Fixed with `.dockerignore` |
| **Frontend Config** | Medium | `VITE_API_URL` is baked into the image at build time. | ℹ️ Documented below |

---

## 🚀 Production Deployment Guide

### 1. Prerequisites
Ensure the model is trained and validated locally before building the image. The build will fail if the model is missing.

```bash
# Verify model exists
ls -l models/malicious_content_detector_calibrated.pkl
```

### 2. Building for Production

Use the standard `docker-compose` to build, or build images manually for registry pushing.

**Backend:**
```bash
docker build -t malicious-content-detection:latest .
```

**Frontend:**
```bash
# You MUST specify the API URL at build time
docker build -t malicious-content-detection-frontend:latest \
  --build-arg VITE_API_URL=https://api.your-domain.com \
  ./frontend
```

### 3. Running in Production

Use the `docker-compose.prod.yml` file which implements resource limits, read-only filesystems, and strict security options.

```bash
# Set secrets via environment variables
export API_KEY="prod-secret-key-complex-value"
export ALLOWED_ORIGINS='["https://ui.your-domain.com"]'

# Deploy
docker-compose -f docker-compose.prod.yml up -d
```

### 4. Operational Monitoring

- **Logs**: Ship container logs (stdout/stderr) to your ELK/Splunk stack. They are already in JSON format.
- **Metrics**: Scrape `http://<backend-ip>:8000/metrics` with Prometheus.
- **Health**: Configure your load balancer to check `http://<backend-ip>:8000/health`.

### 5. Security Checklist
- [ ] Run behind a reverse proxy (NGINX/Traefik) for TLS termination.
- [ ] Ensure `API_KEY` is high-entropy and rotated regularly.
- [ ] Restrict `ALLOWED_ORIGINS` to your actual frontend domain.
- [ ] Monitor CPU/Memory usage against the limits defined in `docker-compose.prod.yml`.
