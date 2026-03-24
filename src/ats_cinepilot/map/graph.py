from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Iterable


@dataclass(slots=True)
class Node:
    node_id: str
    x: float
    z: float


@dataclass(slots=True)
class Edge:
    edge_id: str
    start_node_id: str
    end_node_id: str
    points: list[tuple[float, float]]
    speed_limit_mps: float | None = None
    road_class: str = "unknown"
    metadata: dict = field(default_factory=dict)

    @property
    def length_m(self) -> float:
        return polyline_length(self.points)


def polyline_length(points: Iterable[tuple[float, float]]) -> float:
    pts = list(points)
    if len(pts) < 2:
        return 0.0
    total = 0.0
    for a, b in zip(pts[:-1], pts[1:]):
        total += math.dist(a, b)
    return total


class RoadGraph:
    def __init__(
        self,
        nodes: dict[str, Node],
        edges: dict[str, Edge],
        metadata: dict | None = None,
    ) -> None:
        self.nodes = nodes
        self.edges = edges
        self.metadata = dict(metadata or {})
        self._outgoing_by_node: dict[str, list[str]] = {}
        self._incoming_by_node: dict[str, list[str]] = {}
        for edge in edges.values():
            self._outgoing_by_node.setdefault(edge.start_node_id, []).append(edge.edge_id)
            self._incoming_by_node.setdefault(edge.end_node_id, []).append(edge.edge_id)

    def outgoing_edges(self, edge_id: str) -> list[Edge]:
        edge = self.edges[edge_id]
        ids = self._outgoing_by_node.get(edge.end_node_id, [])
        return [self.edges[eid] for eid in ids]

    def edge_heading_start(self, edge_id: str) -> float:
        edge = self.edges[edge_id]
        if len(edge.points) < 2:
            return 0.0
        (x1, z1), (x2, z2) = edge.points[0], edge.points[1]
        return math.atan2(z2 - z1, x2 - x1)

    def edge_heading_end(self, edge_id: str) -> float:
        edge = self.edges[edge_id]
        if len(edge.points) < 2:
            return 0.0
        (x1, z1), (x2, z2) = edge.points[-2], edge.points[-1]
        return math.atan2(z2 - z1, x2 - x1)
