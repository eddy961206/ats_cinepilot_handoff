import json

from ats_cinepilot.map.cache import load_graph_cache, save_graph_cache
from ats_cinepilot.map.graph import Edge, Node, RoadGraph


def test_graph_cache_round_trip_preserves_metadata_and_compact_json(tmp_path):
    path = tmp_path / "graph.json"
    graph = RoadGraph(
        nodes={
            "a": Node(node_id="a", x=1.5, z=2.5),
            "b": Node(node_id="b", x=4.5, z=5.5),
        },
        edges={
            "e1": Edge(
                edge_id="e1",
                start_node_id="a",
                end_node_id="b",
                points=[(1.5, 2.5), (4.5, 5.5)],
                speed_limit_mps=12.0,
                road_class="trucksim_demo_graph",
                metadata={"direction": "f"},
            )
        },
        metadata={
            "graph_source": "trucksim_demo_graph_region",
            "alignment_mode": "ats_absolute_identity",
            "crop_radius_m": 8000.0,
        },
    )

    save_graph_cache(graph, path, indent=None)

    raw = path.read_text(encoding="utf-8")
    assert "\n" not in raw

    loaded = load_graph_cache(path)
    assert loaded.metadata == graph.metadata
    assert loaded.nodes["a"].x == 1.5
    assert loaded.edges["e1"].metadata["direction"] == "f"
    assert json.loads(raw)["metadata"]["alignment_mode"] == "ats_absolute_identity"
