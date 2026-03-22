from __future__ import annotations

import math
from dataclasses import dataclass

from ats_cinepilot.domain.types import MatchedEdge, PreviewPath, PreviewPoint, RouteHint, TelemetryFrame
from ats_cinepilot.map.graph import RoadGraph

from .branch_selector import BranchSelector


def _curvature(a: tuple[float, float], b: tuple[float, float], c: tuple[float, float]) -> float:
    ax, ay = a
    bx, by = b
    cx, cy = c
    ab = math.dist(a, b)
    bc = math.dist(b, c)
    ca = math.dist(c, a)
    denom = ab * bc * ca
    if denom == 0:
        return 0.0
    area2 = abs((bx - ax) * (cy - ay) - (by - ay) * (cx - ax))
    return (2.0 * area2) / denom


@dataclass
class PreviewPlannerConfig:
    horizon_m: float = 180.0
    default_speed_cap_mps: float = 25.0


class PreviewPlanner:
    def __init__(self, graph: RoadGraph, branch_selector: BranchSelector, config: PreviewPlannerConfig) -> None:
        self.graph = graph
        self.branch_selector = branch_selector
        self.config = config

    def build_path(
        self,
        frame: TelemetryFrame,
        matched: MatchedEdge,
        hint: RouteHint,
    ) -> PreviewPath:
        horizon = self.config.horizon_m
        selected_branch = self.branch_selector.choose(
            matched.edge_id,
            current_heading=frame.pose.yaw_rad,
            hint=hint,
        )

        sampled: list[tuple[float, float]] = []
        distance_left = horizon
        edge_id = matched.edge_id
        first_edge = True
        current_progress = matched.progress_m

        while distance_left > 0 and edge_id:
            edge = self.graph.edges[edge_id]
            pts = edge.points
            sampled_on_edge, consumed = self._slice_edge_points(pts, current_progress if first_edge else 0.0, distance_left)
            if sampled_on_edge:
                if sampled and sampled_on_edge[0] == sampled[-1]:
                    sampled.extend(sampled_on_edge[1:])
                else:
                    sampled.extend(sampled_on_edge)
            distance_left -= consumed
            first_edge = False
            current_progress = 0.0

            outgoing = self.graph.outgoing_edges(edge_id)
            if not outgoing:
                break
            if selected_branch and any(e.edge_id == selected_branch for e in outgoing):
                edge_id = selected_branch
                selected_branch = None
            else:
                edge_id = outgoing[0].edge_id

        points: list[PreviewPoint] = []
        for i, point in enumerate(sampled):
            if 0 < i < len(sampled) - 1:
                curv = _curvature(sampled[i - 1], sampled[i], sampled[i + 1])
            else:
                curv = 0.0
            points.append(
                PreviewPoint(
                    x=point[0],
                    z=point[1],
                    curvature=curv,
                    speed_cap_mps=self.config.default_speed_cap_mps,
                )
            )

        confidence = min(1.0, 0.5 * matched.confidence + 0.5 * max(0.0, hint.confidence))
        return PreviewPath(points=points, horizon_m=horizon, branch_id=selected_branch, confidence=confidence)

    def _slice_edge_points(
        self,
        pts: list[tuple[float, float]],
        start_progress_m: float,
        limit_m: float,
    ) -> tuple[list[tuple[float, float]], float]:
        if len(pts) < 2:
            return pts, 0.0

        out = [pts[0]]
        traversed = 0.0
        consumed = 0.0
        started = start_progress_m <= 0.0

        for a, b in zip(pts[:-1], pts[1:]):
            seg_len = math.dist(a, b)
            next_traversed = traversed + seg_len

            if not started and next_traversed < start_progress_m:
                traversed = next_traversed
                continue

            if not started:
                ratio = (start_progress_m - traversed) / max(seg_len, 1e-6)
                sx = a[0] + (b[0] - a[0]) * ratio
                sz = a[1] + (b[1] - a[1]) * ratio
                out = [(sx, sz)]
                started = True

            if consumed + seg_len > limit_m:
                ratio = (limit_m - consumed) / max(seg_len, 1e-6)
                lx = a[0] + (b[0] - a[0]) * ratio
                lz = a[1] + (b[1] - a[1]) * ratio
                out.append((lx, lz))
                consumed = limit_m
                break

            out.append(b)
            consumed += seg_len
            traversed = next_traversed

        return out, consumed
