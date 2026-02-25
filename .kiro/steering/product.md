# Product Overview

## What is this system?

**Malicious Content Detection System** is an internal security tooling prototype for AI testing and red-team workflows. It's an ML-based API service that detects abusive and malicious content (prompt injection, jailbreaks, policy violations) before it reaches downstream systems.

## Core Purpose

- Detect prompts attempting to manipulate systems (prompt injection, jailbreak intent)
- Provide calibrated probability scores and risk-level decisions
- Support both real-time API predictions and batch processing
- Deploy in isolated, on-premise, or VPC environments where data cannot leave the boundary

## Key Features

1. **Real-Time Prediction API** (`/v1/predict`)
   - Single or batch text classification
   - Returns: label (BENIGN/MALICIOUS), probability, risk level, recommended action

2. **Batch Processing** (`/v1/batch`)
   - CSV file upload for bulk scoring
   - Optimized with parallelization for large datasets

3. **Observability**
   - Prometheus metrics at `/metrics`
   - JSON structured logging with correlation IDs
   - Health checks at `/health`

4. **React Frontend Dashboard**
   - Manual validation and testing
   - Batch CSV upload interface
   - Connection panel for API authentication

## Model Architecture

- **Vectorizer**: TF-IDF (10k features, 1-2 grams)
- **Classifier**: Logistic Regression (C=10, lbfgs solver)
- **Calibration**: Sigmoid calibration for reliable probabilities
- **Decision Threshold**: 0.52 (optimized for F1 score)
- **Performance**: ROC AUC 0.9999 on MPDD dataset (39,234 examples, 50/50 balanced)

> **Demo Dataset Note**: The public dataset used here is exceptionally clean and well-separated, resulting in near-perfect metrics (99.99% AUC). This demonstrates the methodology but not the magnitude of improvement typical in production. Real-world enterprise datasets with noisier, more ambiguous content typically show 85-92% AUC, with calibration reducing error from ~0.18 to ~0.04.

## Deployment Model

- **Docker-based**: Multi-stage builds, non-root user execution
- **API-first design**: Primary interface is FastAPI service
- **Security-hardened**: Model integrity verification, input sanitization, HMAC signing, rate limiting
- **Production-ready**: Circuit breaker, audit logging, security headers

## Important Notes

- The demo uses a public dataset emphasizing jailbreak/prompt injection detection
- Real-world deployments should use organization-specific datasets
- System is designed for internal use; not a substitute for comprehensive safety enforcement
- Requires API key authentication; supports zero-downtime key rotation
