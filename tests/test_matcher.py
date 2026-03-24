import pytest

from ats_cinepilot.domain.types import Pose2D, TelemetryFrame
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
