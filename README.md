# Malicious Content Detection API

A production-ready API for detecting malicious content with real-time predictions, batch processing, and monitoring. Uses a large public dataset (~464k entries) with balanced benign and malicious labels.

## 🔥 Features

### Production-Ready API
- **Real-time predictions** with calibrated probabilities
- **Batch processing** for CSV files (analyst workflows)
- **Monitoring endpoint** (`/metrics`) with performance stats
- **Docker containerized for easy deployment

## 🚀 Quick Start

### Local Development
```bash
# Clone repository
git clone https://github.com/junwenleong/malicious-content-detection-system.git
cd malicious-content-detection-system

# Install dependencies
pip install -r requirements.txt

# Start the API
uvicorn api.app:app --reload --port 8000
```

### Using Docker
```bash
# Build and run
docker build -t malicious-content-detector .
docker run -p 8000:8000 malicious-content-detector
```

## 📊 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API information |
| `/predict` | POST | Single text prediction |
| `/batch` | POST | Batch CSV predictions |
| `/health` | GET | Health check |
| `/metrics` | GET | Monitoring metrics |

### Example Usage
**Single Prediction:**
```bash
curl -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{"texts": ["Hello world", "Test message here"]}'
```

**Batch Prediction:**
```bash
curl -X POST "http://localhost:8000/batch" \
  -F "file=@your_data.csv" \
  -o predictions.csv
```

## 🏗️ Architecture

**Two-stage detection approach:**
1. **Stage 1**: Real-time FastAPI predictions
2. **Stage 2**: Batch CSV processing for analysts

**Key design decisions:**
- TF-IDF features + logistic regression
- Hyperparameter tuning via GridSearchCV
- Model calibration for reliable probabilities


## 🔧 Technical Stack

- **Backend**: FastAPI, Uvicorn
- **ML**: scikit-learn, pandas, numpy
- **Deployment**: Docker, joblib
- **Monitoring**: Custom metrics endpoint, request logging

## 📚 Documentation

- [Deployment Guide](docs/DEPLOYMENT.md) - Production patterns and decisions
- [API Documentation](http://localhost:8000/docs) - Interactive OpenAPI docs
- [Model Training](notebooks/amalicious_content_detection_analysis.ipynb) - Full analysis notebook

## 🎓 Experience Context

*This project demonstrates production deployment patterns implemented for an agency. Due to data sensitivity, the actual production code and data cannot be shared. This repository implements identical architecture using public datasets for malicious content detection.*

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details

---
**Designed with production-ready ML practices.**


---
**Note:** Model files (`.pkl`) are excluded from Git due to size. Run `notebooks/abuse_detection_analysis.ipynb` to train the model, or download from [Releases] when available.
