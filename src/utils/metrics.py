from collections import defaultdict
from datetime import datetime
from typing import Dict, List
from prometheus_client import Counter, Histogram

# Global Prometheus Metrics
PREDICTION_COUNT = Counter("prediction_total", "Total Predictions", ["label"])
PREDICTION_LATENCY = Histogram("prediction_duration_seconds", "Prediction Latency")
ERROR_COUNT = Counter("prediction_errors_total", "Total Prediction Errors")


class Metrics:
    def __init__(self) -> None:
        self.total_requests = 0
        self.total_predictions = 0
        self.predictions_by_class: Dict[str, int] = defaultdict(int)
        self.total_latency = 0.0
        self.errors = 0
        self.start_time = datetime.now()

    def record_prediction(self, label: str, latency: float) -> None:
        self.total_requests += 1
        self.total_predictions += 1
        self.predictions_by_class[label] += 1
        self.total_latency += latency
        PREDICTION_COUNT.labels(label=label).inc()
        PREDICTION_LATENCY.observe(latency)

    def record_batch(self, labels: List[str], latency: float) -> None:
        self.total_requests += 1
        self.total_predictions += len(labels)
        for label in labels:
            self.predictions_by_class[label] += 1
            PREDICTION_COUNT.labels(label=label).inc()
        self.total_latency += latency
        PREDICTION_LATENCY.observe(latency)

    def record_error(self) -> None:
        self.errors += 1
        ERROR_COUNT.inc()

    def get_stats(self) -> Dict[str, object]:
        uptime = (datetime.now() - self.start_time).total_seconds()
        avg_latency = (
            self.total_latency / self.total_requests if self.total_requests > 0 else 0
        )

        return {
            "uptime_seconds": uptime,
            "total_requests": self.total_requests,
            "total_predictions": self.total_predictions,
            "predictions_by_class": dict(self.predictions_by_class),
            "average_latency_ms": avg_latency * 1000,
            "errors": self.errors,
            "requests_per_second": self.total_requests / uptime if uptime > 0 else 0,
        }
