from __future__ import annotations

from pathlib import Path

from ats_cinepilot.bridge.scs_telemetry import ReplayTelemetrySource


def load_replay_source(path: str | Path) -> ReplayTelemetrySource:
    source = ReplayTelemetrySource(path)
    source.connect()
    return source
