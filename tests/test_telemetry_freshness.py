from ats_cinepilot.domain.types import Pose2D, TelemetryFrame
from ats_cinepilot.ops.telemetry_health import TelemetryFreshnessTracker


def _frame(game_tick: int) -> TelemetryFrame:
    return TelemetryFrame(
        mono_time_s=float(game_tick),
        game_tick=game_tick,
        paused=False,
        speed_mps=10.0,
        speed_limit_mps=20.0,
        nav_distance_m=100.0,
        pose=Pose2D(0.0, 0.0, 0.0),
    )


def test_freshness_tracker_resets_when_game_tick_advances(monkeypatch):
    samples = iter([100.0, 100.1])
    monkeypatch.setattr("ats_cinepilot.ops.telemetry_health.time.monotonic", lambda: next(samples))

    tracker = TelemetryFreshnessTracker(timeout_ms=250)
    first = tracker.observe(_frame(1))
    second = tracker.observe(_frame(2))

    assert first == 0.0
    assert second == 0.0
    assert tracker.is_stale(second) is False


def test_freshness_tracker_goes_stale_when_game_tick_stops(monkeypatch):
    samples = iter([100.0, 100.4])
    monkeypatch.setattr("ats_cinepilot.ops.telemetry_health.time.monotonic", lambda: next(samples))

    tracker = TelemetryFreshnessTracker(timeout_ms=250)
    tracker.observe(_frame(1))
    freshness_ms = tracker.observe(_frame(1))

    assert freshness_ms >= 400.0
    assert tracker.is_stale(freshness_ms) is True
