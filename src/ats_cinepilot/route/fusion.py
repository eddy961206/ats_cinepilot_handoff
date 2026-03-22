from __future__ import annotations

import math

from ats_cinepilot.domain.types import MatchedEdge, RouteHint
from ats_cinepilot.perception.confidence import fused_confidence


def compute_route_confidence(
    map_match_confidence: float,
    hud_conf: float,
    path_overlap: float,
    heading_consistency: float,
) -> float:
    return fused_confidence(
        map_match_confidence=map_match_confidence,
        hud_conf=hud_conf,
        path_overlap=path_overlap,
        heading_consistency=heading_consistency,
    )


def build_effective_route_hint(
    raw_hint: RouteHint,
    matched: MatchedEdge | None,
    branch_candidate_count: int,
) -> RouteHint:
    if matched is None:
        return raw_hint

    branch_continuity = _branch_continuity_score(raw_hint, branch_candidate_count)
    heading_consistency = max(0.0, 1.0 - (abs(matched.heading_error_rad) / (math.pi / 4.0)))
    fused = compute_route_confidence(
        map_match_confidence=matched.confidence,
        hud_conf=raw_hint.confidence,
        path_overlap=max(raw_hint.path_overlap, branch_continuity),
        heading_consistency=heading_consistency,
    )
    effective_confidence = max(raw_hint.confidence, fused)
    effective_source = raw_hint.source
    if effective_confidence > raw_hint.confidence and raw_hint.source == "none":
        effective_source = "map_fallback"

    return RouteHint(
        source=effective_source,
        turn_bias=raw_hint.turn_bias,
        path_overlap=max(raw_hint.path_overlap, branch_continuity),
        next_branch_id=raw_hint.next_branch_id,
        confidence=effective_confidence,
    )


def _branch_continuity_score(raw_hint: RouteHint, branch_candidate_count: int) -> float:
    if branch_candidate_count <= 1:
        return 1.0
    if raw_hint.next_branch_id and raw_hint.confidence >= 0.55:
        return 0.85
    if abs(raw_hint.turn_bias) >= 0.35 and raw_hint.confidence >= 0.55:
        return 0.65
    return 0.0
