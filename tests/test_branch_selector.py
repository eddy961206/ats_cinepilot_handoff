from ats_cinepilot.domain.types import RouteHint
from ats_cinepilot.map.graph import Edge, Node, RoadGraph
from ats_cinepilot.planner.branch_selector import BranchSelector, BranchSelectorConfig


def _graph():
    nodes = {
        "a": Node("a", 0, 0),
        "b": Node("b", 10, 0),
        "c": Node("c", 20, 10),
        "d": Node("d", 20, -10),
    }
    edges = {
        "ab": Edge("ab", "a", "b", [(0, 0), (10, 0)], road_class="highway"),
        "bc": Edge("bc", "b", "c", [(10, 0), (20, 10)], road_class="highway"),
        "bd": Edge("bd", "b", "d", [(10, 0), (20, -10)], road_class="highway"),
    }
    return RoadGraph(nodes, edges)


def test_branch_selector_prefers_right_turn_for_positive_bias():
    graph = _graph()
    selector = BranchSelector(graph, BranchSelectorConfig())
    chosen = selector.choose(
        current_edge_id="ab",
        current_heading=0.0,
        hint=RouteHint(source="hud", turn_bias=0.9, path_overlap=0.0, next_branch_id=None, confidence=0.8),
    )
    assert chosen == "bc"
