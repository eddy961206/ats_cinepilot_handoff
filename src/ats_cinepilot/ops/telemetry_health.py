from __future__ import annotations

import time

from ats_cinepilot.domain.types import TelemetryFrame


class TelemetryFreshnessTracker:
    def __init__(self, timeout_ms: int) -> None:
        self.timeout_ms = float(timeout_ms)
        self._last_tick: int | None = None
        self._last_progress_time_s: float | None = None

    def observe(self, frame: TelemetryFrame) -> float:
        now = time.monotonic()
        if self._last_tick != frame.game_tick or self._last_progress_time_s is None:
            self._last_tick = frame.game_tick
            self._last_progress_time_s = now
            return 0.0
        return max(0.0, (now - self._last_progress_time_s) * 1000.0)

    def is_stale(self, freshness_ms: float) -> bool:
        return freshness_ms > self.timeout_ms
