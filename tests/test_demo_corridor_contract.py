from ats_cinepilot.map.cache import load_graph_cache
from ats_cinepilot.ops.demo_corridor import (
    build_curated_corridor_graph,
    fit_contract_to_live_pose,
    load_demo_corridor_contract,
)


def test_load_demo_dense_corridor_contract_reads_expected_sequence():
    contract = load_demo_corridor_contract("configs/corridors/demo_dense_curated_corridor.yaml")

    assert contract.corridor_name == "dense_curated_freeway_demo"
    assert contract.graph_source == "curated_dense_local_corridor_graph"
    assert contract.alignment_mode == "ats_absolute_identity"
    assert contract.start_edge_id == "dense_seg_01"
    assert contract.end_edge_id == "dense_seg_04"
    assert contract.translation_world_x_m == 0.0
    assert contract.translation_world_z_m == 0.0
    assert [edge.edge_id for edge in contract.ordered_edges] == [
        "dense_seg_01",
        "dense_seg_02",
        "dense_seg_03",
        "dense_seg_04",
    ]


def test_build_curated_corridor_graph_orients_edges_forward_and_contiguous():
    contract = load_demo_corridor_contract("configs/corridors/demo_dense_curated_corridor.yaml")
    graph = build_curated_corridor_graph(contract)

    assert graph.metadata["graph_source"] == "curated_dense_local_corridor_graph"
    assert graph.metadata["alignment_mode"] == "ats_absolute_identity"
    assert list(graph.edges) == [
        "dense_seg_01",
        "dense_seg_02",
        "dense_seg_03",
        "dense_seg_04",
    ]

    continuations = graph.continuation_traversals("dense_seg_01", "forward")
    assert [(t.edge_id, t.travel_direction) for t in continuations] == [("dense_seg_02", "forward")]
    continuations = graph.continuation_traversals("dense_seg_02", "forward")
    assert [(t.edge_id, t.travel_direction) for t in continuations] == [("dense_seg_03", "forward")]
    continuations = graph.continuation_traversals("dense_seg_03", "forward")
    assert [(t.edge_id, t.travel_direction) for t in continuations] == [("dense_seg_04", "forward")]
    assert graph.continuation_traversals("dense_seg_04", "forward") == []

    first = graph.edges["dense_seg_01"].points
    second = graph.edges["dense_seg_02"].points
    third = graph.edges["dense_seg_03"].points
    fourth = graph.edges["dense_seg_04"].points
    assert first[-1] == second[0]
    assert second[-1] == third[0]
    assert third[-1] == fourth[0]


def test_exported_dense_demo_graph_cache_matches_contract():
    contract = load_demo_corridor_contract("configs/corridors/demo_dense_curated_corridor.yaml")
    expected = build_curated_corridor_graph(contract)
    actual = load_graph_cache("data/maps/cache/demo_dense_curated_corridor_graph.json")

    assert actual.metadata == expected.metadata
    assert list(actual.edges) == list(expected.edges)
    assert actual.edges["dense_seg_01"].points == expected.edges["dense_seg_01"].points
    assert actual.edges["dense_seg_04"].points == expected.edges["dense_seg_04"].points


def test_fit_contract_to_live_pose_applies_translation_and_start_window():
    contract = load_demo_corridor_contract("configs/corridors/demo_dense_curated_corridor.yaml")

    fitted, projection = fit_contract_to_live_pose(
        contract,
        world_x=-74385.31327819824,
        world_z=27291.640899658203,
        graph_cache_path="data/maps/cache/runtime_dense_demo_graph.json",
        corridor_name="dense_curated_freeway_demo_runtime",
        start_progress_backtrack_m=10.0,
        start_progress_ahead_m=20.0,
    )

    assert projection.spec.edge_id == "dense_seg_01"
    assert round(projection.translation_world_x_m, 3) == 15.823
    assert round(projection.translation_world_z_m, 3) == -1.670
    assert fitted.corridor_name == "dense_curated_freeway_demo_runtime"
    assert fitted.graph_cache_path == "data/maps/cache/runtime_dense_demo_graph.json"
    assert fitted.start_edge_id == "dense_seg_01"
    assert round(fitted.start_progress_min_m or 0.0, 2) == 150.88
    assert round(fitted.start_progress_max_m or 0.0, 2) == 180.88
    assert fitted.translation_world_x_m == projection.translation_world_x_m
    assert fitted.translation_world_z_m == projection.translation_world_z_m
    assert fitted.ordered_edges[0].start_world_x != contract.ordered_edges[0].start_world_x

    graph = build_curated_corridor_graph(fitted)
    first_edge = graph.edges["dense_seg_01"]
    assert round(first_edge.points[0][0] - contract.ordered_edges[0].start_world_x, 3) == 15.823
    assert round(first_edge.points[0][1] - contract.ordered_edges[0].start_world_z, 3) == -1.670
