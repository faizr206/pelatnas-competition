from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from threading import Lock
from time import time


@dataclass(frozen=True)
class LoginRateLimitStatus:
    limited: bool
    retry_after_seconds: int


class LoginRateLimiter:
    def __init__(self) -> None:
        self._failures: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def check(self, *, key: str, window_seconds: int, max_attempts: int) -> LoginRateLimitStatus:
        now = time()
        with self._lock:
            attempts = self._prune(key=key, now=now, window_seconds=window_seconds)
            if len(attempts) < max_attempts:
                return LoginRateLimitStatus(limited=False, retry_after_seconds=0)

            retry_after_seconds = max(1, int(attempts[0] + window_seconds - now))
            return LoginRateLimitStatus(
                limited=True,
                retry_after_seconds=retry_after_seconds,
            )

    def record_failure(self, *, key: str, window_seconds: int) -> None:
        now = time()
        with self._lock:
            attempts = self._prune(key=key, now=now, window_seconds=window_seconds)
            attempts.append(now)

    def clear(self, *, key: str) -> None:
        with self._lock:
            self._failures.pop(key, None)

    def reset(self) -> None:
        with self._lock:
            self._failures.clear()

    def _prune(self, *, key: str, now: float, window_seconds: int) -> deque[float]:
        attempts = self._failures[key]
        cutoff = now - window_seconds
        while attempts and attempts[0] < cutoff:
            attempts.popleft()
        if not attempts:
            self._failures.pop(key, None)
            attempts = self._failures[key]
        return attempts


login_rate_limiter = LoginRateLimiter()
