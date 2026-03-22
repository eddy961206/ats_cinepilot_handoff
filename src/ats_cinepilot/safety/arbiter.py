from __future__ import annotations

from dataclasses import dataclass

from ats_cinepilot.domain.enums import DisengageReason
from ats_cinepilot.domain.types import (
    MatchedEdge,
    PreviewPath,
    RouteHint,
    SafetyDecision,
    TelemetryFrame,
    VehicleCommand,
)

from .rules import (
    check_curvature_overspeed,
    check_match_confidence,
    check_paused,
    check_route_confidence,
    check_tracking_errors,
)


@dataclass
class SafetyConfig:
    min_map_match_confidence: float = 0.60
    min_route_confidence: float = 0.55
    max_cross_track_error_m: float = 1.20
    max_heading_error_deg: float = 18.0
    overspeed_curve_margin_kph: float = 8.0


class RuleBasedSafetyPolicy:
    def __init__(self, config: SafetyConfig) -> None:
        self.config = config

    def evaluate(
        self,
        frame: TelemetryFrame | None,
        matched: MatchedEdge | None,
        hint: RouteHint | None,
        path: PreviewPath | None,
        command: VehicleCommand | None,
    ) -> SafetyDecision:
        _ = command
        for check in (
            check_paused(frame),
            check_match_confidence(matched, self.config.min_map_match_confidence),
            check_tracking_errors(
                matched,
                self.config.max_cross_track_error_m,
                self.config.max_heading_error_deg,
            ),
            check_route_confidence(hint, self.config.min_route_confidence),
            check_curvature_overspeed(
                frame,
                path,
                self.config.overspeed_curve_margin_kph,
            ),
        ):
            if check is not None:
                return SafetyDecision(False, reason=check)
        return SafetyDecision(True, reason=DisengageReason.NONE)
