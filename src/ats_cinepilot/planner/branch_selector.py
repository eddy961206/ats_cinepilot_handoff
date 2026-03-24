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

    def choose(
        self,
        current_edge_id: str,
        current_heading: float,
        hint: RouteHint,
        current_travel_direction: str = "forward",
    ) -> str | None:
        continuations = self.graph.continuation_traversals(current_edge_id, current_travel_direction)
        if not continuations:
            return None
        if len(continuations) == 1:
            return continuations[0].edge_id

        best_id: str | None = None
        best_score = -1e9
        current_edge = self.graph.edges[current_edge_id]
        current_exit_heading = self.graph.edge_heading_end(current_edge_id, current_travel_direction)

        for traversal in continuations:
            edge = self.graph.edges[traversal.edge_id]
            cand_heading = self.graph.edge_heading_start(traversal.edge_id, traversal.travel_direction)
            cand_bias = _normalize_bias_from_heading(current_heading, cand_heading)
            route_bias_score = 1.0 - abs(cand_bias - hint.turn_bias)
            heading_score = 1.0 - min(1.0, abs(cand_heading - current_exit_heading) / math.pi)
            continuity_score = 1.0 if edge.road_class == current_edge.road_class else 0.5
            score = (
                self.config.route_bias_weight * route_bias_score
                + self.config.heading_weight * heading_score
                + self.config.continuity_weight * continuity_score
            )
            if score > best_score:
                best_score = score
                best_id = traversal.edge_id
        return best_id
