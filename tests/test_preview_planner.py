import pytest

from ats_cinepilot.domain.types import Pose2D, RouteHint, TelemetryFrame
from ats_cinepilot.map.graph import Edge, Node, RoadGraph
from ats_cinepilot.map.matcher import MatcherConfig, SimplePoseMatcher
from ats_cinepilot.map.spatial_index import SimpleSpatialIndex
from ats_cinepilot.planner.branch_selector import BranchSelector, BranchSelectorConfig
from ats_cinepilot.planner.preview_path import PreviewPlanner, PreviewPlannerConfig


def _reverse_rescue_preview_graph() -> RoadGraph:
    nodes = {
        "a": Node("a", 0.0, 0.0),
        "b": Node("b", 10.0, 0.0),
        "c": Node("c", 20.0, 0.0),
        "d": Node("d", -10.0, 10.0),
    }
    edges = {
        "ba": Edge("ba", "b", "a", [(10.0, 0.0), (0.0, 0.0)], road_class="highway"),
        "cb": Edge("cb", "c", "b", [(20.0, 0.0), (10.0, 0.0)], road_class="highway"),
        "ad": Edge("ad", "a", "d", [(0.0, 0.0), (-10.0, 10.0)], road_class="local"),
    }
    return RoadGraph(nodes, edges)


def test_reverse_rescued_match_builds_preview_in_actual_travel_direction():
    graph = _reverse_rescue_preview_graph()
    matcher = SimplePoseMatcher(
        graph,
        SimpleSpatialIndex(graph),
        MatcherConfig(query_radius_m=15.0),
    )
    planner = PreviewPlanner(
        graph,
        BranchSelector(graph, BranchSelectorConfig()),
        PreviewPlannerConfig(horizon_m=25.0),
    )
    frame = TelemetryFrame(
        mono_time_s=0.0,
        game_tick=1,
        paused=False,
        speed_mps=8.0,
        speed_limit_mps=20.0,
        nav_distance_m=100.0,
        pose=Pose2D(world_x=2.0, world_z=0.5, yaw_rad=0.0),
    )

    matched = matcher.match(frame, None)

    assert matched is not None
    assert matched.edge_id == "ba"

    path = planner.build_path(
        frame,
        matched,
        RouteHint(source="none", turn_bias=0.0, path_overlap=0.0, next_branch_id=None, confidence=0.0),
    )

    assert path.points
    xs = [point.x for point in path.points]
    assert xs[0] == pytest.approx(2.0, abs=0.25)
    assert max(xs) > 15.0
    assert min(xs) >= 0.0
