import time
import threading


class CircuitBreaker:
    def __init__(self, failure_threshold: int, cooldown_seconds: float) -> None:
        self.failure_threshold = max(failure_threshold, 1)
        self.cooldown_seconds = max(cooldown_seconds, 0.1)
        self.failure_count = 0
        self.open_until = 0.0
        self._lock = threading.Lock()

    def allow_request(self) -> bool:
        with self._lock:
            # If open_until is in the future, we are OPEN
            if time.monotonic() < self.open_until:
                return False
            # If open_until is in the past, we are CLOSED or HALF-OPEN (implicitly)
            return True

    def record_success(self) -> None:
        with self._lock:
            self.failure_count = 0
            self.open_until = 0.0

    def record_failure(self) -> None:
        with self._lock:
            self.failure_count += 1
            if self.failure_count >= self.failure_threshold:
                self.open_until = time.monotonic() + self.cooldown_seconds
                # Reset failure count so we don't immediately re-open after cooldown
                # unless another failure happens
                self.failure_count = 0

    @property
    def state(self) -> str:
        with self._lock:
            if time.monotonic() < self.open_until:
                return "open"
            if self.failure_count > 0:
                return "half-open"  # Not technically true half-open but indicates fragility
            return "closed"
