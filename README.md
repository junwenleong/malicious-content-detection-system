# 🚀 Production-Grade Abuse Detection API

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.9+-blue?style=for-the-badge&logo=python)](https://www.python.org/)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-F7931E?style=for-the-badge&logo=scikit-learn)](https://scikit-learn.org/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker)](https://www.docker.com/)

A production-ready abuse detection system with real-time API, batch processing, and comprehensive monitoring. Demonstrates deployment patterns used in national security contexts using public datasets.

## 🔥 Features

### Production-Ready API
- **Real-time predictions** with calibrated probabilities
- **Batch processing** for CSV files (analyst workflows)
- **Rate limiting** (100 requests/minute per IP)
- **Monitoring endpoint** (`/metrics`) with performance stats
- **Health checks** and request logging middleware

### ML Engineering
- **Calibrated logistic regression** with F1-optimized threshold (0.45)
- **TF-IDF features** with hyperparameter tuning
- **Model serialization** with joblib for deployment
- **Precision-recall optimization** (92% recall, 88% precision)

### Deployment Ready
- **Docker containerization** with production-ready config
- **FastAPI** with auto-generated OpenAPI docs
- **Production monitoring patterns** (metrics, logging, health checks)

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
# Build and run
docker build -t abuse-detector .
docker run -p 8000:8000 abuse-detector
```

## 📊 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API information |
| `/predict` | POST | Real-time abuse detection |
| `/batch` | POST | Process CSV files in bulk |
| `/health` | GET | Service health status |
| `/metrics` | GET | Performance metrics |

### Example Usage
**Single Prediction:**
```bash
curl -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{"texts": ["Hello world", "Test message here"]}'
```

**Batch Processing:**
```bash
curl -X POST "http://localhost:8000/batch" \
  -F "file=@your_data.csv" \
  -o predictions.csv
```

## 🏗️ Architecture

**Two-stage detection approach:**
1. **Stage 1**: Real-time classification (FastAPI endpoint)
2. **Stage 2**: Batch session analysis (CSV processing)

**Key design decisions:**
- **0.45 threshold** (F1-optimized, 92% recall, 88% precision)
- **Production monitoring** (request logging, metrics endpoint)
- **Rate limiting** (prevent system abuse)
- **Batch CSV processing** (analyst-friendly workflows)

## 🎯 Use Cases

- **API Abuse Detection**: Monitor user-generated content
- **Trust & Safety**: Identify abusive patterns
- **Security Monitoring**: Detect malicious intent
- **Content Moderation**: Automated policy violation detection

## 📈 Performance (Test Set: 3,586 samples)

| Metric | Value |
|--------|-------|
| **Accuracy** | 91% |
| **Recall (ABUSIVE)** | 93% |
| **Precision (ABUSIVE)** | 89% |
| **F1 Score** | 91% |
| **Latency** | < 50ms per prediction |

## 🔧 Technical Stack

- **Backend**: FastAPI, Uvicorn
- **ML**: scikit-learn, pandas, numpy
- **Deployment**: Docker, joblib
- **Monitoring**: Custom metrics endpoint, request logging

## 📚 Documentation

- [Deployment Guide](docs/DEPLOYMENT.md) - Production patterns and decisions
- [API Documentation](http://localhost:8000/docs) - Interactive OpenAPI docs
- [Model Training](notebooks/01_explore.ipynb) - Full analysis notebook

## 🎓 Experience Context

*This project demonstrates production deployment patterns implemented for an agency. Due to data sensitivity, the actual production code and data cannot be shared. This repository implements identical architecture using public datasets.*

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details

---
**Built with production ML considerations that followed a real deployment.**

---
**Note:** Model files (`.pkl`) are excluded from Git due to size. Run `notebooks/01_explore.ipynb` to train the model, or download from [Releases] when available.
