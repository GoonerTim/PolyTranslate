"""Thread-safe rate limiter for free translation APIs."""

from __future__ import annotations

import logging
import threading
import time

logger = logging.getLogger(__name__)


class RateLimiter:
    """Enforces minimum interval between requests. Thread-safe."""

    def __init__(self, min_interval: float = 1.0) -> None:
        self._min_interval = min_interval
        self._last_request_time = 0.0
        self._lock = threading.Lock()

    @property
    def min_interval(self) -> float:
        return self._min_interval

    def wait(self) -> None:
        """Block until enough time has passed since the last request."""
        with self._lock:
            now = time.time()
            elapsed = now - self._last_request_time
            if elapsed < self._min_interval:
                delay = self._min_interval - elapsed
                logger.debug("Rate limiter: sleeping %.2fs", delay)
                time.sleep(delay)
            self._last_request_time = time.time()

    def reset(self) -> None:
        """Reset the last request timestamp."""
        with self._lock:
            self._last_request_time = 0.0
