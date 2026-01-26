# Production Deployment Notes

## Background
I built this to show the architecture and deployment approach I used for a malicious content detection system at a national agency. 
The actual system handles sensitive data, so I can't share the code or datasets. This version uses a public dataset of ~464k entries with balanced benign/malicious labels.


## Key Decisions We Made

### Two-Stage Processing
We split detection into two parts:
- **Real-time API** (\`/predict\`) - checks each request immediately with calibrated probabilities
- **Batch analysis** (\`/batch\`) - processes logs overnight for deeper patterns
This let us optimize each part separately - speed for the API, thoroughness for batch jobs.

### How We Found the 0.540 Threshold
The 0.540 threshold wasn't arbitrary - it was determined using ~464k public dataset entries and calibrated probabilities, balancing high recall for malicious content with minimal false positives.


- ~99.8% recall for malicious content (catching violations)
- ~99.9% precision for benign content (manageable false positive rate)


### Monitoring That Actually Helps
We built:
- Request logging (to debug issues)
- Metrics endpoint (to track performance)
- Health checks (to know if the system is alive)
Simple, but crucial for maintaining a reliable service.

### Operational stuff that matters
- Rate limiting (so the system couldn't be abused)
- Input validation (so malformed requests don't crash things)
- Batch CSV processing (because analysts work with spreadsheets)
- Clear error messages (so we know what went wrong)

## Problems we solved

### Updating Models Without Downtime
We could not take the service offline to update the model. Our fix: versioned endpoints and gradual rollouts.

### Handling Traffic Spikes
Some days were quiet, others had 10x normal traffic. Rate limiting and proper scaling handled this.

### Reducing Analyst Workload
Analysts were occupied with too many false positives. The junior analysts assigned to such work would likely not be able the handle the workload. The 0.540 threshold (backed by actual performance data) gave us the best balance:
- ~99.8% recall for malicious content (catching violations)
- ~99.9% precision for benign content (manageable false positive rate)
These results are based on the public dataset used for this demo (~464k entries, balanced labels).


## Principles we followed

This code uses similar patterns implemented in production:
- FastAPI structure
- sklearn/joblib model handling  
- Same monitoring approach
- Same operational thinking
- **Same data-driven threshold selection** (based on actual confusion matrices)

The differences from the real system:
- Public datasets instead of operational data
- Simplified auth (production had stricter controls)
- Smaller scale (production handled much more traffic)

## Quick Test Commands

```bash
# Start it up
uvicorn api.app:app --reload --port 8000

# Check it's alive
curl http://localhost:8000/health

# See performance stats  
curl http://localhost:8000/metrics

# Test a prediction
curl -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{"texts": ["Test message here"]}'

# Process a CSV file
curl -X POST "http://localhost:8000/batch" \
  -F "file=@your_file.csv" \
  -o predictions.csv
```

## Skills This Demonstrates

- Building production APIs with FastAPI
- **Data-driven decision making** (actual confusion matrix analysis)
- Deploying ML models with measurable performance trade-offs
- Monitoring and observability that helps troubleshoot
- Rate limiting and input validation (security thinking)
- Batch processing for real workflows
- Containerization with Docker

## What I'd Discuss in Interviews

- Why we prioritized recall over precision for malicious content in a security context
- How we validated thresholds with real test data (not just theoretical)
- The operational impact of threshold choices on analyst workload
- How separating real-time and batch processing optimized both
- Security considerations for production ML systems

## Final Note

This project reflects real production thinking: decisions backed by data (confusion matrices), architecture driven by operational needs, and trade-offs made consciously (recall over precision for security). The 0.540 threshold wasn't arbitrary - it was determined using ~464k public dataset entries and calibrated probabilities, balancing high recall for malicious content with minimal false positives.

