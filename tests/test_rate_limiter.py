"""Tests for RateLimiter utility."""

from __future__ import annotations

import threading
import time

from app.utils.rate_limiter import RateLimiter


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
