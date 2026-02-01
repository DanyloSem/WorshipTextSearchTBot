from __future__ import annotations

import asyncio
import time


class PcoRateLimiter:
    """
    Обмежувач частоти запитів: не більше max_requests за window_seconds (ковзне вікно).

    Використовується перед кожним HTTP-запитом до PCO API, щоб не перевищити ліміт.
    """

    def __init__(self, max_requests: int = 90, window_seconds: float = 20.0) -> None:
        """
        Args:
            max_requests: Максимум запитів у вікні.
            window_seconds: Довжина вікна в секундах.
        """
        self._max_requests = max_requests
        self._window_seconds = window_seconds
        self._timestamps: list[float] = []
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """
        Блокує до моменту, коли можна виконати ще один запит у межах ліміту.

        Після виходу викликач може виконати один HTTP-запит; час виклику враховується у вікні.
        """
        async with self._lock:
            while True:
                now = time.monotonic()
                cutoff = now - self._window_seconds
                self._timestamps = [t for t in self._timestamps if t > cutoff]
                if len(self._timestamps) < self._max_requests:
                    self._timestamps.append(now)
                    return
                oldest = min(self._timestamps)
                wait_seconds = oldest + self._window_seconds - now
                if wait_seconds > 0:
                    await asyncio.sleep(wait_seconds)
