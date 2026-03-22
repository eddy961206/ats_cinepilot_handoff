from __future__ import annotations

import math

from ats_cinepilot.domain.enums import DisengageReason
from ats_cinepilot.domain.types import MatchedEdge, PreviewPath, RouteHint, TelemetryFrame


def check_paused(frame: TelemetryFrame | None):
    if frame and frame.paused:
        return DisengageReason.PAUSED
    return None


def check_match_confidence(matched: MatchedEdge | None, minimum: float):
    if matched is None or matched.confidence < minimum:
        return DisengageReason.MATCH_LOST
    return None


def check_route_confidence(hint: RouteHint | None, minimum: float):
    if hint is None or hint.confidence < minimum:
        return DisengageReason.ROUTE_CONFIDENCE_LOW
    return None


def check_tracking_errors(
    matched: MatchedEdge | None,
    max_cross_track_error_m: float,
    max_heading_error_deg: float,
):
    if matched is None:
        return DisengageReason.MATCH_LOST
    if matched.cross_track_error_m > max_cross_track_error_m:
        return DisengageReason.MATCH_LOST
    if abs(math.degrees(matched.heading_error_rad)) > max_heading_error_deg:
        return DisengageReason.MATCH_LOST
    return None


def check_curvature_overspeed(
    frame: TelemetryFrame | None,
    path: PreviewPath | None,
    overspeed_margin_kph: float,
):
    if frame is None or path is None or not path.points:
        return None
    hard_cap = min(p.speed_cap_mps for p in path.points[:20])
    if frame.speed_mps > hard_cap + overspeed_margin_kph / 3.6:
        return DisengageReason.CURVATURE_OVERSPEED
    return None
