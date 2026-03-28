import pytest

from ats_cinepilot.map.curated_corridor import extract_curated_corridor_graph
from ats_cinepilot.map.graph import Edge, Node, RoadGraph


def _graph() -> RoadGraph:
    nodes = {
        "n0": Node("n0", 0.0, 0.0),
        "n1": Node("n1", 10.0, 0.0),
        "n2": Node("n2", 20.0, 4.0),
        "n3": Node("n3", 28.0, 10.0),
    }
    edges = {
        "edge_a": Edge("edge_a", "n0", "n1", [(0.0, 0.0), (10.0, 0.0)], road_class="local"),
        "edge_b": Edge("edge_b", "n1", "n2", [(10.0, 0.0), (20.0, 4.0)], road_class="local"),
        "edge_c": Edge("edge_c", "n2", "n3", [(20.0, 4.0), (28.0, 10.0)], road_class="local"),
    }
    return RoadGraph(
        nodes=nodes,
        edges=edges,
        metadata={
            "graph_source": "trucksim_local_geojson_region",
            "alignment_mode": "ats_absolute_identity",
            "export_toolchain": "unit_test",
        },
    )


def test_extract_curated_corridor_graph_keeps_only_selected_connected_edges():
    graph = extract_curated_corridor_graph(
        _graph(),
        corridor_name="dense_demo_curve",
        edge_sequence=["edge_a", "edge_b"],
        graph_source="curated_dense_local_corridor_graph",
        alignment_mode="ats_absolute_identity",
        source_cache_path="data/maps/cache/source.json",
    )

    assert set(graph.nodes) == {"n0", "n1", "n2"}
    assert list(graph.edges) == ["edge_a", "edge_b"]
    assert graph.metadata["graph_source"] == "curated_dense_local_corridor_graph"
    assert graph.metadata["alignment_mode"] == "ats_absolute_identity"
    assert graph.metadata["graph_kind"] == "curated_demo_corridor"
    assert graph.metadata["corridor_name"] == "dense_demo_curve"
    assert graph.metadata["approved_edge_sequence"] == ["edge_a", "edge_b"]
    assert graph.metadata["source_cache_path"] == "data/maps/cache/source.json"
    assert graph.metadata["source_graph_source"] == "trucksim_local_geojson_region"


def test_extract_curated_corridor_graph_rejects_non_connected_edge_sequence():
    graph = _graph()
    graph.edges["edge_d"] = Edge(
        "edge_d",
        "n0",
        "n3",
        [(0.0, 0.0), (28.0, 10.0)],
        road_class="local",
    )

    with pytest.raises(ValueError, match="connected"):
        extract_curated_corridor_graph(
            graph,
            corridor_name="broken_demo_curve",
            edge_sequence=["edge_b", "edge_d"],
            graph_source="curated_dense_local_corridor_graph",
            alignment_mode="ats_absolute_identity",
        )
