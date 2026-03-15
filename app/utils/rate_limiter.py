"""Thread-safe rate limiter for free translation APIs."""

from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable

import httpx

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


def retry_with_backoff(
    rate_limiter: RateLimiter,
    request_fn: Callable[[], httpx.Response],
    service_name: str,
    max_retries: int = 3,
    base_delay: float = 2.0,
) -> httpx.Response:
    """Execute request_fn with rate limiting, retry on errors and 429s."""
    for attempt in range(max_retries + 1):
        rate_limiter.wait()
        try:
            response = request_fn()
        except httpx.RequestError as e:
            if attempt == max_retries:
                raise ValueError(f"{service_name} request failed: {e}") from e
            logger.warning(
                "%s request error, retry %d/%d: %s", service_name, attempt + 1, max_retries, e
            )
            time.sleep(base_delay * (2**attempt))
            continue

        if response.status_code == 429:
            if attempt < max_retries:
                delay = base_delay * (2**attempt)
                logger.warning(
                    "%s rate limited (429), retry %d/%d after %.1fs",
                    service_name,
                    attempt + 1,
                    max_retries,
                    delay,
                )
                time.sleep(delay)
                continue
            raise ValueError(
                f"{service_name} rate limit exceeded. Please try again later or use an API key."
            )

        return response

    raise ValueError(f"{service_name}: Maximum retries exceeded")
