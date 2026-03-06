from collections import defaultdict
from datetime import datetime, timezone
import threading
from typing import Dict
from prometheus_client import Counter, Histogram

# Global Prometheus Metrics
PREDICTION_COUNT = Counter("prediction_total", "Total Predictions", ["label"])
PREDICTION_LATENCY = Histogram("prediction_duration_seconds", "Prediction Latency")
ERROR_COUNT = Counter("prediction_errors_total", "Total Prediction Errors")


class Metrics:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.total_requests = 0
        self.total_predictions = 0
        self.predictions_by_class: Dict[str, int] = defaultdict(int)
        self.total_latency = 0.0
        self.errors = 0
        self.start_time = datetime.now(timezone.utc)

    def record_prediction(self, label: str, latency: float) -> None:
        with self._lock:
            self.total_requests += 1
            self.total_predictions += 1
            self.predictions_by_class[label] += 1
            self.total_latency += latency
        PREDICTION_COUNT.labels(label=label).inc()
        PREDICTION_LATENCY.observe(latency)

    def record_error(self) -> None:
        with self._lock:
            self.errors += 1
        ERROR_COUNT.inc()

    def get_stats(self) -> Dict[str, object]:
        with self._lock:
            uptime = (datetime.now(timezone.utc) - self.start_time).total_seconds()
            avg_latency = (
                self.total_latency / self.total_requests
                if self.total_requests > 0
                else 0
            )
            return {
                "uptime_seconds": uptime,
                "total_requests": self.total_requests,
                "total_predictions": self.total_predictions,
                "predictions_by_class": dict(self.predictions_by_class),
                "average_latency_ms": avg_latency * 1000,
                "errors": self.errors,
                "requests_per_second": (
                    self.total_requests / uptime if uptime > 0 else 0
                ),
            }
