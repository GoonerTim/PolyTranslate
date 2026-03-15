"""Tests for RateLimiter utility."""

from __future__ import annotations

import threading
import time
from unittest.mock import MagicMock

import httpx
import pytest

from app.utils.rate_limiter import RateLimiter, retry_with_backoff


class TestRateLimiter:
    def test_first_call_no_delay(self):
        limiter = RateLimiter(min_interval=1.0)
        start = time.time()
        limiter.wait()
        elapsed = time.time() - start
        assert elapsed < 0.1

    def test_enforces_min_interval(self):
        limiter = RateLimiter(min_interval=0.2)
        limiter.wait()
        start = time.time()
        limiter.wait()
        elapsed = time.time() - start
        assert elapsed >= 0.15  # small tolerance

    def test_no_delay_after_interval_passed(self):
        limiter = RateLimiter(min_interval=0.1)
        limiter.wait()
        time.sleep(0.15)
        start = time.time()
        limiter.wait()
        elapsed = time.time() - start
        assert elapsed < 0.05

    def test_reset(self):
        limiter = RateLimiter(min_interval=0.5)
        limiter.wait()
        limiter.reset()
        start = time.time()
        limiter.wait()
        elapsed = time.time() - start
        assert elapsed < 0.05

    def test_thread_safety(self):
        limiter = RateLimiter(min_interval=0.1)
        timestamps: list[float] = []
        lock = threading.Lock()

        def call():
            limiter.wait()
            with lock:
                timestamps.append(time.time())

        threads = [threading.Thread(target=call) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        timestamps.sort()
        for i in range(1, len(timestamps)):
            gap = timestamps[i] - timestamps[i - 1]
            assert gap >= 0.08  # small tolerance for 0.1s interval

    def test_min_interval_property(self):
        limiter = RateLimiter(min_interval=2.5)
        assert limiter.min_interval == 2.5

    def test_default_interval(self):
        limiter = RateLimiter()
        assert limiter.min_interval == 1.0


class TestRetryWithBackoff:
    def test_success_on_first_try(self) -> None:
        limiter = RateLimiter(min_interval=0.0)
        response = MagicMock(spec=httpx.Response)
        response.status_code = 200
        result = retry_with_backoff(limiter, lambda: response, "test", max_retries=2)
        assert result is response

    def test_retries_on_request_error(self) -> None:
        limiter = RateLimiter(min_interval=0.0)
        response = MagicMock(spec=httpx.Response)
        response.status_code = 200
        call_count = 0

        def flaky() -> httpx.Response:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise httpx.RequestError("timeout")
            return response

        result = retry_with_backoff(limiter, flaky, "test", max_retries=3, base_delay=0.01)
        assert result is response
        assert call_count == 3

    def test_max_retries_exceeded_request_error(self) -> None:
        limiter = RateLimiter(min_interval=0.0)

        def always_fail() -> httpx.Response:
            raise httpx.RequestError("down")

        with pytest.raises(ValueError, match="request failed"):
            retry_with_backoff(limiter, always_fail, "svc", max_retries=1, base_delay=0.01)

    def test_retries_on_429(self) -> None:
        limiter = RateLimiter(min_interval=0.0)
        ok_response = MagicMock(spec=httpx.Response)
        ok_response.status_code = 200
        rate_response = MagicMock(spec=httpx.Response)
        rate_response.status_code = 429
        call_count = 0

        def rate_limited() -> httpx.Response:
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                return rate_response
            return ok_response

        result = retry_with_backoff(limiter, rate_limited, "test", max_retries=3, base_delay=0.01)
        assert result.status_code == 200

    def test_429_max_retries_raises(self) -> None:
        limiter = RateLimiter(min_interval=0.0)
        response = MagicMock(spec=httpx.Response)
        response.status_code = 429

        with pytest.raises(ValueError, match="rate limit exceeded"):
            retry_with_backoff(limiter, lambda: response, "svc", max_retries=1, base_delay=0.01)

    def test_max_retries_zero_unreachable_path(self) -> None:
        """Line 83: the final raise after for-loop exhaustion."""
        limiter = RateLimiter(min_interval=0.0)
        # This is a defensive unreachable line. To hit it we'd need
        # the loop to complete without returning or raising, which
        # can't happen in normal flow. Instead we just verify it
        # doesn't happen with max_retries=0 and success.
        response = MagicMock(spec=httpx.Response)
        response.status_code = 200
        result = retry_with_backoff(limiter, lambda: response, "svc", max_retries=0)
        assert result is response
