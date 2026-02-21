import time
from collections import defaultdict, deque
from typing import Deque, Dict


class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, Deque[float]] = defaultdict(deque)

    def is_allowed(self, client_id: str) -> bool:
        """
        Check if request is allowed and record the attempt.
        """
        now = time.time()
        window_start = now - self.window_seconds
        timestamps = self.requests[client_id]

        while timestamps and timestamps[0] < window_start:
            timestamps.popleft()

        if len(timestamps) >= self.max_requests:
            return False

        timestamps.append(now)
        return True

    def is_blocked(self, client_id: str) -> bool:
        """
        Check if client is currently blocked without recording an attempt.
        """
        now = time.time()
        window_start = now - self.window_seconds
        timestamps = self.requests[client_id]

        while timestamps and timestamps[0] < window_start:
            timestamps.popleft()

        return len(timestamps) >= self.max_requests

    def record_attempt(self, client_id: str) -> None:
        """
        Record an attempt for a client.
        """
        now = time.time()
        self.requests[client_id].append(now)
