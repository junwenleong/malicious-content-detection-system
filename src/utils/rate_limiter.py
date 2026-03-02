import time
import threading
from collections import defaultdict, deque
from typing import Deque, Dict

# Maximum number of unique client IDs to track before forcing a full cleanup.
# Prevents unbounded memory growth under high-cardinality IP churn.
_MAX_TRACKED_CLIENTS = 10_000


class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, Deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def _cleanup(self, client_id: str, now: float) -> None:
        """Remove expired timestamps for a client.

        This prevents memory leaks by removing old timestamps outside the window.
        Must be called with lock held.

        Args:
            client_id: Client identifier
            now: Current timestamp
        """
        window_start = now - self.window_seconds
        timestamps = self.requests[client_id]

        # Remove all timestamps older than the window
        while timestamps and timestamps[0] < window_start:
            timestamps.popleft()

    def _evict_stale_clients(self, now: float) -> None:
        """Remove clients with no recent activity to prevent memory bloat.

        Called when tracked client count exceeds _MAX_TRACKED_CLIENTS.
        Must be called with lock held.
        """
        window_start = now - self.window_seconds
        stale = [
            cid for cid, ts in self.requests.items() if not ts or ts[-1] < window_start
        ]
        for cid in stale:
            del self.requests[cid]

    def is_allowed(self, client_id: str) -> bool:
        """Check if request is allowed and record the attempt."""
        now = time.time()
        with self._lock:
            # Evict stale clients if we're tracking too many unique IPs
            if len(self.requests) > _MAX_TRACKED_CLIENTS:
                self._evict_stale_clients(now)

            self._cleanup(client_id, now)
            timestamps = self.requests[client_id]
            if len(timestamps) >= self.max_requests:
                return False
            timestamps.append(now)
            return True

    def is_blocked(self, client_id: str) -> bool:
        """Check if client is currently blocked without recording an attempt."""
        now = time.time()
        with self._lock:
            self._cleanup(client_id, now)
            return len(self.requests[client_id]) >= self.max_requests

    def record_attempt(self, client_id: str) -> None:
        """Record an attempt for a client."""
        now = time.time()
        with self._lock:
            self.requests[client_id].append(now)
