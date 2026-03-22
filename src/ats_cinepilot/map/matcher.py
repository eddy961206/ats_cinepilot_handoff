from __future__ import annotations

import math
from dataclasses import dataclass
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


class SimplePoseMatcher:
    def __init__(self, graph: RoadGraph, spatial_index: SimpleSpatialIndex, config: MatcherConfig) -> None:
        self.graph = graph
        self.spatial_index = spatial_index
        self.config = config

    def match(
        self,
        frame: TelemetryFrame,
        previous: Optional[MatchedEdge],
    ) -> Optional[MatchedEdge]:
        candidates = self.spatial_index.nearby_edges(frame.pose, self.config.query_radius_m)
        if not candidates:
            return None

        best_score = float("inf")
        best_match: Optional[MatchedEdge] = None

        for candidate in candidates[:12]:
            edge = self.graph.edges[candidate.edge_id]
            progress_m, cross_track_error_m, heading_error_rad = self._measure_on_edge(frame, edge.edge_id)
            score = (
                self.config.distance_weight * cross_track_error_m
                + self.config.heading_weight * abs(heading_error_rad) * 10.0
            )
            if previous and previous.edge_id == edge.edge_id:
                score -= self.config.hysteresis_weight * 5.0

            if score < best_score:
                conf = max(0.0, min(1.0, 1.0 - score / max(self.config.query_radius_m, 1.0)))
                best_score = score
                best_match = MatchedEdge(
                    edge_id=edge.edge_id,
                    lane_id=None,
                    progress_m=progress_m,
                    cross_track_error_m=cross_track_error_m,
                    heading_error_rad=heading_error_rad,
                    confidence=conf,
                )
        return best_match

    def _measure_on_edge(self, frame: TelemetryFrame, edge_id: str) -> tuple[float, float, float]:
        edge = self.graph.edges[edge_id]
        pts = edge.points
        traversed = 0.0
        best_dist = float("inf")
        best_progress = 0.0
        best_heading_error = 0.0

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
            traversed += seg_len

        return best_progress, best_dist, best_heading_error
