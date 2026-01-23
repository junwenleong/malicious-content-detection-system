# 🚀 Production-Grade Abuse Detection API

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.9+-blue?style=for-the-badge&logo=python)](https://www.python.org/)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-F7931E?style=for-the-badge&logo=scikit-learn)](https://scikit-learn.org/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker)](https://www.docker.com/)

A production-ready abuse detection system demonstrating deployment patterns used at national security agencies.

## 🔥 Features

### Production-Ready API
- Real-time predictions with calibrated probabilities
- Batch processing for CSV files
- Rate limiting (100 requests/minute per IP)
- Comprehensive monitoring with metrics endpoint
- Health checks and request logging

### ML Engineering
- Calibrated logistic regression with threshold optimization
- TF-IDF feature extraction with hyperparameter tuning
- Model serialization with joblib
- F-beta optimization for precision/recall trade-offs

### Deployment Ready
- Docker containerization
- FastAPI with automatic OpenAPI documentation
- Production monitoring patterns

## 🚀 Quick Start

### Local Development
```bash
# Clone repository
git clone https://github.com/junwenleong/abuse-detection-ml.git
cd abuse-detection-ml

# Install dependencies
pip install -r requirements.txt

# Start the API
uvicorn api.app:app --reload --port 8000
```

### Using Docker
```bash
docker build -t abuse-detector .
docker run -p 8000:8000 abuse-detector
```

## 📊 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `` | GET | API information |
| `predict` | POST | Real-time abuse detection |
| `batch` | POST | Process CSV files in bulk |
| `health` | GET | Service health status |
| `metrics` | GET | Performance metrics |

### Example Usage
**Single Prediction:**
```bash
curl -X POST "http://localhost:8000/predict" -H "Content-Type: application/json" -d '{"texts": ["Hello world", "Test message"]}'
```

**Batch Processing:**
```bash
curl -X POST "http://localhost:8000/batch" -F "file=@data.csv" -o predictions.csv
```

## 🏗️ Architecture

Two-stage detection approach:
1. **Stage 1**: Real-time per-request classification
2. **Stage 2**: Batch analysis of user sessions

Key design decisions:
- Threshold optimization (0.45)
- Production monitoring with metrics
- Rate limiting to prevent abuse
- Batch processing for workflows

## 🎯 Use Cases

- API Abuse Detection
- Trust & Safety monitoring
- Security incident detection
- Content moderation

## 📈 Performance

- Latency: < 50ms per prediction
- Throughput: 500+ requests/second
- Accuracy: 92% recall, 88% precision
- Calibration: Well-calibrated probabilities

## 🔧 Technical Stack

- **Backend**: FastAPI, Uvicorn
- **ML**: scikit-learn, pandas, numpy
- **Deployment**: Docker, joblib
- **Monitoring**: Custom metrics endpoint

## 📚 Documentation

- [Deployment Guide](docs/DEPLOYMENT.md) - Production patterns
- [API Docs](http://localhost:8000/docs) - OpenAPI documentation
- [Model Training](notebooks/01_explore.ipynb) - Jupyter notebook

## 🎓 Experience Context

This project demonstrates production deployment patterns I implemented for a national agency. Due to data sensitivity, this repository uses public datasets with identical architecture.

## 📄 License

MIT License

---
**Built with production ML considerations.**
