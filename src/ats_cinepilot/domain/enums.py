from __future__ import annotations

from enum import Enum, auto


class Mode(Enum):
    OFF = auto()
    CALIBRATING = auto()
    SHADOW = auto()
    ARMED = auto()
    ACTIVE = auto()
    DISENGAGING = auto()
    FAULT = auto()


class DisengageReason(Enum):
    NONE = auto()
    USER_OVERRIDE = auto()
    TELEMETRY_STALE = auto()
    HUD_INVALID = auto()
    ROUTE_CONFIDENCE_LOW = auto()
    MATCH_LOST = auto()
    CURVATURE_OVERSPEED = auto()
    DEMO_GUARD = auto()
    WRITE_FAILED = auto()
    PAUSED = auto()
    EXCEPTION = auto()
