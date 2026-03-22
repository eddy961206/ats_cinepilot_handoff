from __future__ import annotations

import math
from dataclasses import dataclass

from ats_cinepilot.domain.types import RouteHint
from ats_cinepilot.map.graph import RoadGraph


def _normalize_bias_from_heading(current_heading: float, candidate_heading: float) -> float:
    diff = (candidate_heading - current_heading + math.pi) % (2 * math.pi) - math.pi
    return max(-1.0, min(1.0, diff / (math.pi / 2.0)))


@dataclass
class BranchSelectorConfig:
    heading_weight: float = 0.45
    route_bias_weight: float = 0.45
    continuity_weight: float = 0.10


class BranchSelector:
    def __init__(self, graph: RoadGraph, config: BranchSelectorConfig) -> None:
        self.graph = graph
        self.config = config

    def choose(self, current_edge_id: str, current_heading: float, hint: RouteHint) -> str | None:
        outgoing = self.graph.outgoing_edges(current_edge_id)
        if not outgoing:
            return None
        if len(outgoing) == 1:
            return outgoing[0].edge_id

        best_id: str | None = None
        best_score = -1e9
        current_edge = self.graph.edges[current_edge_id]

        for edge in outgoing:
            cand_heading = self.graph.edge_heading_start(edge.edge_id)
            cand_bias = _normalize_bias_from_heading(current_heading, cand_heading)
            route_bias_score = 1.0 - abs(cand_bias - hint.turn_bias)
            heading_score = 1.0 - min(1.0, abs(cand_heading - self.graph.edge_heading_end(current_edge_id)) / math.pi)
            continuity_score = 1.0 if edge.road_class == current_edge.road_class else 0.5
            score = (
                self.config.route_bias_weight * route_bias_score
                + self.config.heading_weight * heading_score
                + self.config.continuity_weight * continuity_score
            )
            if score > best_score:
                best_score = score
                best_id = edge.edge_id
        return best_id
