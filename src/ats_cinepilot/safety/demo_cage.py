from __future__ import annotations

import math
from dataclasses import dataclass

from ats_cinepilot.domain.types import MatchedEdge, PreviewPath, RouteHint, TelemetryFrame


@dataclass(slots=True)
class DemoCageConfig:
    enabled: bool = False
    corridor_name: str = "disabled"
    approved_graph_source: str = ""
    approved_alignment_mode: str = ""
    approved_edge_ids: tuple[str, ...] = ()
    allowed_travel_directions: tuple[str, ...] = ("forward",)
    allowed_direction_confidence_states: tuple[str, ...] = ("confident",)
    allowed_pose_sources: tuple[str, ...] = ("authoritative_absolute",)
    allowed_heading_sources: tuple[str, ...] = ("absolute_position_delta", "absolute_position_hold")
    min_progress_m: float | None = None
    max_progress_m: float | None = None
    min_match_confidence: float = 0.97
    min_route_confidence: float = 0.65
    max_cross_track_error_m: float = 0.30
    max_heading_error_deg: float = 8.0
    max_nearest_edge_distance_m: float = 0.30
    max_speed_mps: float = 4.0
    max_graph_candidate_count: int = 1
    require_anchor_locked: bool = True
    require_no_discontinuity: bool = True
    arm_consecutive_frames: int = 10


@dataclass(slots=True)
class DemoCageDecision:
    allow_control: bool
    reason: str
    armed: bool
    qualifying_frames: int


class DemoSafetyCage:
    def __init__(self, config: DemoCageConfig) -> None:
        self.config = config
        self._qualifying_frames = 0

    def evaluate(
        self,
        *,
        frame: TelemetryFrame | None,
        matched: MatchedEdge | None,
        hint: RouteHint | None,
        path: PreviewPath | None,
        telemetry_state,
        matcher_diagnostics,
        graph_source: str,
        alignment_mode: str,
        control_sink_healthy: bool,
        manual_override_active: bool,
    ) -> DemoCageDecision:
        if not self.config.enabled:
            return DemoCageDecision(True, "disabled", True, self._qualifying_frames)

        failure = self._first_failure(
            frame=frame,
            matched=matched,
            hint=hint,
            path=path,
            telemetry_state=telemetry_state,
            matcher_diagnostics=matcher_diagnostics,
            graph_source=graph_source,
            alignment_mode=alignment_mode,
            control_sink_healthy=control_sink_healthy,
            manual_override_active=manual_override_active,
        )
        if failure is not None:
            self._qualifying_frames = 0
            return DemoCageDecision(False, failure, False, self._qualifying_frames)

        self._qualifying_frames += 1
        if self._qualifying_frames < max(1, self.config.arm_consecutive_frames):
            return DemoCageDecision(False, "arming", False, self._qualifying_frames)
        return DemoCageDecision(True, "armed", True, self._qualifying_frames)

    def _first_failure(
        self,
        *,
        frame: TelemetryFrame | None,
        matched: MatchedEdge | None,
        hint: RouteHint | None,
        path: PreviewPath | None,
        telemetry_state,
        matcher_diagnostics,
        graph_source: str,
        alignment_mode: str,
        control_sink_healthy: bool,
        manual_override_active: bool,
    ) -> str | None:
        _ = path
        if not control_sink_healthy:
            return "control_sink_unhealthy"
        if manual_override_active:
            return "manual_override"
        if graph_source != self.config.approved_graph_source:
            return "graph_source_mismatch"
        if alignment_mode != self.config.approved_alignment_mode:
            return "alignment_mode_mismatch"
        if frame is None:
            return "telemetry_missing"
        if frame.paused:
            return "paused"
        if frame.speed_mps > self.config.max_speed_mps:
            return "speed_cap_exceeded"
        if getattr(telemetry_state, "pose_source", None) not in self.config.allowed_pose_sources:
            return "pose_source_unapproved"
        if getattr(telemetry_state, "heading_source", None) not in self.config.allowed_heading_sources:
            return "heading_source_unapproved"
        if self.config.require_anchor_locked and not bool(getattr(telemetry_state, "anchor_heading_locked", False)):
            return "anchor_heading_unlocked"
        if self.config.require_no_discontinuity and bool(getattr(telemetry_state, "discontinuity_detected", False)):
            return "discontinuity_active"
        if matched is None:
            return "match_missing"
        if matched.edge_id not in self.config.approved_edge_ids:
            return "outside_corridor_edge"
        if matched.travel_direction not in self.config.allowed_travel_directions:
            return "travel_direction_unapproved"
        if self.config.min_progress_m is not None and matched.progress_m < self.config.min_progress_m:
            return "progress_out_of_bounds"
        if self.config.max_progress_m is not None and matched.progress_m > self.config.max_progress_m:
            return "progress_out_of_bounds"
        if matched.confidence < self.config.min_match_confidence:
            return "match_confidence_low"
        if matched.cross_track_error_m > self.config.max_cross_track_error_m:
            return "cross_track_error_high"
        if abs(math.degrees(matched.heading_error_rad)) > self.config.max_heading_error_deg:
            return "heading_error_high"
        if hint is None or hint.confidence < self.config.min_route_confidence:
            return "route_confidence_low"
        if int(getattr(matcher_diagnostics, "candidate_count", 0)) > self.config.max_graph_candidate_count:
            return "candidate_count_high"
        nearest_edge_distance_m = getattr(matcher_diagnostics, "nearest_edge_distance_m", None)
        if nearest_edge_distance_m is None or float(nearest_edge_distance_m) > self.config.max_nearest_edge_distance_m:
            return "nearest_edge_distance_high"
        if getattr(matcher_diagnostics, "failure_reason", None):
            return "graph_failure"
        if getattr(matcher_diagnostics, "direction_confidence_state", None) not in self.config.allowed_direction_confidence_states:
            return "direction_confidence_unapproved"
        return None
