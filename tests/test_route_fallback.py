from ats_cinepilot.domain.types import MatchedEdge, RouteHint
from ats_cinepilot.route.fusion import build_effective_route_hint


def test_effective_route_hint_uses_map_continuity_on_unambiguous_segment():
    matched = MatchedEdge("ab", None, 12.0, 0.2, 0.01, 0.95)
    raw_hint = RouteHint("none", 0.0, 0.0, None, 0.0)

    effective = build_effective_route_hint(
        raw_hint=raw_hint,
        matched=matched,
        branch_candidate_count=1,
    )

    assert effective.source == "map_fallback"
    assert effective.confidence >= 0.55


def test_effective_route_hint_stays_low_when_branch_is_ambiguous_without_hud():
    matched = MatchedEdge("ab", None, 12.0, 0.2, 0.01, 0.95)
    raw_hint = RouteHint("none", 0.0, 0.0, None, 0.0)

    effective = build_effective_route_hint(
        raw_hint=raw_hint,
        matched=matched,
        branch_candidate_count=2,
    )

    assert effective.confidence < 0.55
