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


@dataclass(slots=True)
class EdgeTraversal:
    edge_id: str
    travel_direction: str


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

    def continuation_traversals(self, edge_id: str, travel_direction: str = "forward") -> list[EdgeTraversal]:
        edge = self.edges[edge_id]
        exit_node_id = edge.end_node_id if travel_direction == "forward" else edge.start_node_id
        traversals: list[EdgeTraversal] = []
        seen: set[tuple[str, str]] = set()
        for next_edge_id in self._outgoing_by_node.get(exit_node_id, []):
            key = (next_edge_id, "forward")
            if next_edge_id == edge_id or key in seen:
                continue
            traversals.append(EdgeTraversal(next_edge_id, "forward"))
            seen.add(key)
        for next_edge_id in self._incoming_by_node.get(exit_node_id, []):
            key = (next_edge_id, "reverse")
            if next_edge_id == edge_id or key in seen:
                continue
            traversals.append(EdgeTraversal(next_edge_id, "reverse"))
            seen.add(key)
        return traversals

    def edge_points(self, edge_id: str, travel_direction: str = "forward") -> list[tuple[float, float]]:
        edge = self.edges[edge_id]
        if travel_direction == "reverse":
            return list(reversed(edge.points))
        return list(edge.points)

    def edge_heading_start(self, edge_id: str, travel_direction: str = "forward") -> float:
        pts = self.edge_points(edge_id, travel_direction)
        if len(pts) < 2:
            return 0.0
        (x1, z1), (x2, z2) = pts[0], pts[1]
        return math.atan2(z2 - z1, x2 - x1)

    def edge_heading_end(self, edge_id: str, travel_direction: str = "forward") -> float:
        pts = self.edge_points(edge_id, travel_direction)
        if len(pts) < 2:
            return 0.0
        (x1, z1), (x2, z2) = pts[-2], pts[-1]
        return math.atan2(z2 - z1, x2 - x1)
