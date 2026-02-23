import time
import threading


class CircuitBreaker:
    def __init__(self, failure_threshold: int, cooldown_seconds: float) -> None:
        self.failure_threshold = max(failure_threshold, 1)
        self.cooldown_seconds = max(cooldown_seconds, 0.1)
        self.failure_count = 0
        self.open_until = 0.0
        self._was_open = False
        self._lock = threading.Lock()

    def allow_request(self) -> bool:
        with self._lock:
            now = time.monotonic()
            if now < self.open_until:
                return False
            # If breaker was open and cooldown expired, enter half-open
            if self._was_open:
                # Allow one probe request in half-open state
                return True
            return True

    def record_success(self) -> None:
        with self._lock:
            self.failure_count = 0
            self.open_until = 0.0
            self._was_open = False

    def record_failure(self) -> None:
        with self._lock:
            self.failure_count += 1
            if self.failure_count >= self.failure_threshold:
                self.open_until = time.monotonic() + self.cooldown_seconds
                self._was_open = True
                self.failure_count = 0

    @property
    def state(self) -> str:
        with self._lock:
            now = time.monotonic()
            if now < self.open_until:
                return "open"
            if self._was_open:
                return "half-open"
            if self.failure_count > 0:
                return "half-open"
            return "closed"
