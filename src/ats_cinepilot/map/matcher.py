from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

from ats_cinepilot.domain.types import MatchedEdge, TelemetryFrame

from .graph import RoadGraph
from .spatial_index import SimpleSpatialIndex, point_segment_distance


def angle_diff_rad(a: float, b: float) -> float:
    diff = (a - b + math.pi) % (2 * math.pi) - math.pi
    return diff


@dataclass
class MatcherConfig:
    query_radius_m: float = 45.0
    heading_weight: float = 0.35
    distance_weight: float = 0.55
    hysteresis_weight: float = 0.10
    continuity_distance_slack_m: float = 1.0
    reverse_heading_min_advantage_m: float = 1.0
    reverse_heading_penalty: float = 0.5


@dataclass
class MatchDiagnostics:
    candidate_count: int = 0
    nearest_edge_distance_m: float | None = None
    failure_reason: str | None = None
    top_candidates: list["CandidateDirectionDiagnostics"] = field(default_factory=list)
    selected_edge_id: str | None = None
    selected_reason: str | None = None
    direction_confidence_state: str | None = None
    selected_score_breakdown: dict[str, float] = field(default_factory=dict)


@dataclass
class CandidateDirectionDiagnostics:
    edge_id: str
    distance_m: float
    edge_heading_rad: float
    vehicle_heading_rad: float
    signed_heading_delta_rad: float
    effective_heading_delta_rad: float
    direction_classification: str
    heading_mode: str
    score_breakdown: dict[str, float]
    total_score: float


@dataclass
class CandidateMeasurement:
    edge_id: str
    progress_m: float
    cross_track_error_m: float
    edge_heading_rad: float
    forward_heading_error_rad: float
    reverse_heading_error_rad: float
    forward_signed_heading_delta_rad: float
    reverse_signed_heading_delta_rad: float
    forward_direction_classification: str
    reverse_direction_classification: str


class SimplePoseMatcher:
    def __init__(self, graph: RoadGraph, spatial_index: SimpleSpatialIndex, config: MatcherConfig) -> None:
        self.graph = graph
        self.spatial_index = spatial_index
        self.config = config
        self.last_diagnostics = MatchDiagnostics()

    def match(
        self,
        frame: TelemetryFrame,
        previous: Optional[MatchedEdge],
    ) -> Optional[MatchedEdge]:
        candidates = self.spatial_index.nearby_edges(frame.pose, self.config.query_radius_m)
        if not candidates:
            self.last_diagnostics = MatchDiagnostics(
                candidate_count=0,
                nearest_edge_distance_m=None,
                failure_reason="no_nearby_edge",
            )
            return None

        best_score = float("inf")
        best_match: Optional[MatchedEdge] = None
        best_candidate: Optional[CandidateDirectionDiagnostics] = None
        nearest_edge_distance_m = candidates[0].distance_m
        candidate_diagnostics: list[tuple[float, CandidateDirectionDiagnostics]] = []
        measured_candidates = [
            self._measure_candidate(frame, candidate.edge_id)
            for candidate in candidates[:12]
        ]
        nearest_candidate_distance_m = min(
            (measured.cross_track_error_m for measured in measured_candidates),
            default=None,
        )
        best_forward_non_opposed_distance = min(
            (
                measured.cross_track_error_m
                for measured in measured_candidates
                if measured.forward_direction_classification != "opposed"
            ),
            default=None,
        )

        for measured in measured_candidates:
            use_reverse_heading = self._should_use_reverse_heading(
                measured,
                best_forward_non_opposed_distance,
            )
            heading_error_rad = (
                measured.reverse_heading_error_rad
                if use_reverse_heading
                else measured.forward_heading_error_rad
            )
            effective_signed_heading_delta_rad = (
                measured.reverse_signed_heading_delta_rad
                if use_reverse_heading
                else measured.forward_signed_heading_delta_rad
            )
            distance_score = self.config.distance_weight * measured.cross_track_error_m
            heading_score = self.config.heading_weight * abs(heading_error_rad) * 10.0
            hysteresis_score = 0.0
            reverse_heading_penalty = self.config.reverse_heading_penalty if use_reverse_heading else 0.0
            score = distance_score + heading_score + reverse_heading_penalty
            if previous and previous.edge_id == measured.edge_id and self._should_apply_hysteresis(
                measured,
                nearest_candidate_distance_m,
            ):
                hysteresis_score = -self.config.hysteresis_weight * 5.0
                score += hysteresis_score

            candidate_diag = CandidateDirectionDiagnostics(
                edge_id=measured.edge_id,
                distance_m=measured.cross_track_error_m,
                edge_heading_rad=measured.edge_heading_rad,
                vehicle_heading_rad=frame.pose.yaw_rad,
                signed_heading_delta_rad=measured.forward_signed_heading_delta_rad,
                effective_heading_delta_rad=effective_signed_heading_delta_rad,
                direction_classification=measured.forward_direction_classification,
                heading_mode="reverse" if use_reverse_heading else "forward",
                score_breakdown={
                    "distance": distance_score,
                    "heading": heading_score,
                    "hysteresis": hysteresis_score,
                    "reverse_heading_penalty": reverse_heading_penalty,
                },
                total_score=score,
            )
            candidate_diagnostics.append((score, candidate_diag))

            if score < best_score:
                conf = max(0.0, min(1.0, 1.0 - score / max(self.config.query_radius_m, 1.0)))
                best_score = score
                best_candidate = candidate_diag
                best_match = MatchedEdge(
                    edge_id=measured.edge_id,
                    lane_id=None,
                    progress_m=measured.progress_m,
                    cross_track_error_m=measured.cross_track_error_m,
                    heading_error_rad=heading_error_rad,
                    confidence=conf,
                )
        sorted_diagnostics = [
            diagnostic for _, diagnostic in sorted(candidate_diagnostics, key=lambda item: item[0])
        ]
        self.last_diagnostics = MatchDiagnostics(
            candidate_count=len(candidates),
            nearest_edge_distance_m=nearest_edge_distance_m,
            failure_reason=None if best_match is not None else "no_match_selected",
            top_candidates=sorted_diagnostics,
            selected_edge_id=best_match.edge_id if best_match is not None else None,
            selected_reason=self._selected_reason(best_candidate) if best_candidate is not None else None,
            direction_confidence_state=(
                self._direction_confidence_state(best_candidate) if best_candidate is not None else None
            ),
            selected_score_breakdown=best_candidate.score_breakdown if best_candidate is not None else {},
        )
        return best_match

    def _measure_on_edge(self, frame: TelemetryFrame, edge_id: str) -> tuple[float, float, float, float]:
        edge = self.graph.edges[edge_id]
        pts = edge.points
        traversed = 0.0
        best_dist = float("inf")
        best_progress = 0.0
        best_heading_error = 0.0
        best_heading = 0.0

        for (ax, az), (bx, bz) in zip(pts[:-1], pts[1:]):
            seg_len = math.dist((ax, az), (bx, bz))
            dist, t = point_segment_distance(
                frame.pose.world_x,
                frame.pose.world_z,
                ax, az, bx, bz,
            )
            if dist < best_dist:
                heading = math.atan2(bz - az, bx - ax)
                best_dist = dist
                best_progress = traversed + seg_len * t
                best_heading_error = angle_diff_rad(frame.pose.yaw_rad, heading)
                best_heading = heading
            traversed += seg_len

        return best_progress, best_dist, best_heading_error, best_heading

    def _measure_candidate(self, frame: TelemetryFrame, edge_id: str) -> CandidateMeasurement:
        progress_m, cross_track_error_m, forward_heading_error_rad, edge_heading_rad = self._measure_on_edge(
            frame,
            edge_id,
        )
        reverse_edge_heading_rad = angle_diff_rad(edge_heading_rad + math.pi, 0.0)
        reverse_heading_error_rad = angle_diff_rad(frame.pose.yaw_rad, reverse_edge_heading_rad)
        forward_signed_heading_delta_rad = angle_diff_rad(frame.pose.yaw_rad, edge_heading_rad)
        reverse_signed_heading_delta_rad = angle_diff_rad(frame.pose.yaw_rad, reverse_edge_heading_rad)
        return CandidateMeasurement(
            edge_id=edge_id,
            progress_m=progress_m,
            cross_track_error_m=cross_track_error_m,
            edge_heading_rad=edge_heading_rad,
            forward_heading_error_rad=forward_heading_error_rad,
            reverse_heading_error_rad=reverse_heading_error_rad,
            forward_signed_heading_delta_rad=forward_signed_heading_delta_rad,
            reverse_signed_heading_delta_rad=reverse_signed_heading_delta_rad,
            forward_direction_classification=self._classify_direction(forward_signed_heading_delta_rad),
            reverse_direction_classification=self._classify_direction(reverse_signed_heading_delta_rad),
        )

    def _should_use_reverse_heading(
        self,
        candidate: CandidateMeasurement,
        best_forward_non_opposed_distance: float | None,
    ) -> bool:
        if candidate.forward_direction_classification != "opposed":
            return False
        if candidate.reverse_direction_classification == "opposed":
            return False
        if best_forward_non_opposed_distance is None:
            return True
        return (
            candidate.cross_track_error_m + self.config.reverse_heading_min_advantage_m
            < best_forward_non_opposed_distance
        )

    def _should_apply_hysteresis(
        self,
        candidate: CandidateMeasurement,
        nearest_candidate_distance_m: float | None,
    ) -> bool:
        if nearest_candidate_distance_m is None:
            return True
        return (
            candidate.cross_track_error_m
            <= nearest_candidate_distance_m + self.config.continuity_distance_slack_m
        )

    def _classify_direction(self, signed_heading_delta_rad: float) -> str:
        abs_delta = abs(signed_heading_delta_rad)
        if abs_delta <= math.pi / 4:
            return "aligned"
        if abs_delta >= (3 * math.pi) / 4:
            return "opposed"
        return "ambiguous"

    def _selected_reason(self, candidate: CandidateDirectionDiagnostics) -> str:
        breakdown = candidate.score_breakdown
        if breakdown["hysteresis"] < 0.0:
            return "continuity"
        if breakdown["heading"] > breakdown["distance"]:
            return "heading"
        return "distance"

    def _direction_confidence_state(self, candidate: CandidateDirectionDiagnostics) -> str:
        if candidate.heading_mode == "reverse":
            return "reverse_heading_rescued"
        if candidate.direction_classification == "aligned":
            return "confident"
        if candidate.direction_classification == "opposed":
            return "opposed_best_available"
        return "ambiguous"
