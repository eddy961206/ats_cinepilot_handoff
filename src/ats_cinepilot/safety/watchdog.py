from __future__ import annotations

import time


class StalenessWatchdog:
    def __init__(self, timeout_ms: int) -> None:
        self.timeout_s = timeout_ms / 1000.0
        self._last_seen_s = None

    def touch(self) -> None:
        self._last_seen_s = time.monotonic()

    def is_stale(self) -> bool:
        if self._last_seen_s is None:
            return True
        return (time.monotonic() - self._last_seen_s) > self.timeout_s
