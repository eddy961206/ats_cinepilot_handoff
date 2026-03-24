import math

import pytest

from ats_cinepilot.domain.types import MatchedEdge, Pose2D, TelemetryFrame
from ats_cinepilot.map.graph import Edge, Node, RoadGraph
from ats_cinepilot.map.matcher import MatcherConfig, SimplePoseMatcher
from ats_cinepilot.map.spatial_index import SimpleSpatialIndex


def _graph():
    nodes = {
        "a": Node("a", 0, 0),
        "b": Node("b", 100, 0),
        "c": Node("c", 100, 100),
    }
    edges = {
        "ab": Edge("ab", "a", "b", [(0, 0), (100, 0)], road_class="highway"),
        "bc": Edge("bc", "b", "c", [(100, 0), (100, 100)], road_class="highway"),
    }
    return RoadGraph(nodes, edges)


def test_matcher_prefers_nearest_edge():
    graph = _graph()
    matcher = SimplePoseMatcher(graph, SimpleSpatialIndex(graph), MatcherConfig(query_radius_m=50.0))
    frame = TelemetryFrame(
        mono_time_s=0.0,
        game_tick=1,
        paused=False,
        speed_mps=10.0,
        speed_limit_mps=20.0,
        nav_distance_m=1000.0,
        pose=Pose2D(world_x=10.0, world_z=3.0, yaw_rad=0.0),
    )
    match = matcher.match(frame, None)
    assert match is not None
    assert match.edge_id == "ab"
    assert match.confidence > 0.5
    assert matcher.last_diagnostics.candidate_count == 1
    assert matcher.last_diagnostics.nearest_edge_distance_m == pytest.approx(3.0)
    assert matcher.last_diagnostics.failure_reason is None


def test_matcher_records_no_nearby_edge_failure():
    graph = _graph()
    matcher = SimplePoseMatcher(graph, SimpleSpatialIndex(graph), MatcherConfig(query_radius_m=10.0))
    frame = TelemetryFrame(
        mono_time_s=0.0,
        game_tick=1,
        paused=False,
        speed_mps=10.0,
        speed_limit_mps=20.0,
        nav_distance_m=1000.0,
        pose=Pose2D(world_x=500.0, world_z=500.0, yaw_rad=0.0),
    )

    match = matcher.match(frame, None)

    assert match is None
    assert matcher.last_diagnostics.candidate_count == 0
    assert matcher.last_diagnostics.failure_reason == "no_nearby_edge"


def test_matcher_records_candidate_direction_diagnostics_and_heading_selection():
    graph = _graph()
    matcher = SimplePoseMatcher(graph, SimpleSpatialIndex(graph), MatcherConfig(query_radius_m=10.0))
    frame = TelemetryFrame(
        mono_time_s=0.0,
        game_tick=1,
        paused=False,
        speed_mps=8.0,
        speed_limit_mps=20.0,
        nav_distance_m=100.0,
        pose=Pose2D(world_x=98.0, world_z=2.0, yaw_rad=0.0),
    )

    match = matcher.match(frame, None)

    assert match is not None
    assert match.edge_id == "ab"
    diagnostics = matcher.last_diagnostics
    assert diagnostics.failure_reason is None
    assert diagnostics.selected_edge_id == "ab"
    assert diagnostics.selected_reason == "distance"
    assert diagnostics.direction_confidence_state == "confident"
    assert len(diagnostics.top_candidates) == 2

    best = diagnostics.top_candidates[0]
    assert best.edge_id == "ab"
    assert best.distance_m == pytest.approx(2.0)
    assert best.edge_heading_rad == pytest.approx(0.0)
    assert best.vehicle_heading_rad == pytest.approx(0.0)
    assert best.signed_heading_delta_rad == pytest.approx(0.0)
    assert best.direction_classification == "aligned"
    assert best.score_breakdown["distance"] == pytest.approx(1.1)
    assert best.score_breakdown["heading"] == pytest.approx(0.0)
    assert best.score_breakdown["hysteresis"] == pytest.approx(0.0)

    other = diagnostics.top_candidates[1]
    assert other.edge_id == "bc"
    assert other.direction_classification == "ambiguous"
    assert other.score_breakdown["heading"] > best.score_breakdown["heading"]


def test_matcher_marks_opposed_best_available_when_hysteresis_keeps_previous_edge():
    graph = _graph()
    matcher = SimplePoseMatcher(graph, SimpleSpatialIndex(graph), MatcherConfig(query_radius_m=10.0))
    frame = TelemetryFrame(
        mono_time_s=0.0,
        game_tick=1,
        paused=False,
        speed_mps=8.0,
        speed_limit_mps=20.0,
        nav_distance_m=100.0,
        pose=Pose2D(world_x=98.0, world_z=2.0, yaw_rad=math.pi),
    )
    previous = MatchedEdge(
        edge_id="ab",
        lane_id=None,
        progress_m=98.0,
        cross_track_error_m=2.0,
        heading_error_rad=0.0,
        confidence=0.9,
    )

    match = matcher.match(frame, previous)

    assert match is not None
    assert match.edge_id == "bc"
    diagnostics = matcher.last_diagnostics
    assert diagnostics.selected_edge_id == "bc"
    assert diagnostics.selected_reason == "heading"
    assert diagnostics.direction_confidence_state == "ambiguous"
    assert diagnostics.top_candidates[0].edge_id == "bc"
    assert diagnostics.top_candidates[0].direction_classification == "ambiguous"
    assert diagnostics.top_candidates[1].edge_id == "ab"
    assert diagnostics.top_candidates[1].direction_classification == "opposed"
    assert diagnostics.top_candidates[1].score_breakdown["hysteresis"] < 0.0
