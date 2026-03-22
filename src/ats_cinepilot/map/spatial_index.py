from __future__ import annotations

import math
from dataclasses import dataclass

from ats_cinepilot.domain.types import Pose2D

from .graph import RoadGraph


@dataclass
class CandidateDistance:
    edge_id: str
    distance_m: float


def point_segment_distance(px: float, pz: float, ax: float, az: float, bx: float, bz: float) -> tuple[float, float]:
    abx = bx - ax
    abz = bz - az
    apx = px - ax
    apz = pz - az
    ab2 = abx * abx + abz * abz
    if ab2 == 0.0:
        return math.dist((px, pz), (ax, az)), 0.0
    t = max(0.0, min(1.0, (apx * abx + apz * abz) / ab2))
    cx = ax + abx * t
    cz = az + abz * t
    return math.dist((px, pz), (cx, cz)), t


class SimpleSpatialIndex:
    def __init__(self, graph: RoadGraph) -> None:
        self.graph = graph

    def nearby_edges(self, pose: Pose2D, radius_m: float) -> list[CandidateDistance]:
        out: list[CandidateDistance] = []
        for edge in self.graph.edges.values():
            best = float("inf")
            pts = edge.points
            for (ax, az), (bx, bz) in zip(pts[:-1], pts[1:]):
                dist, _ = point_segment_distance(
                    pose.world_x, pose.world_z,
                    ax, az, bx, bz,
                )
                if dist < best:
                    best = dist
            if best <= radius_m:
                out.append(CandidateDistance(edge_id=edge.edge_id, distance_m=best))
        out.sort(key=lambda x: x.distance_m)
        return out
