from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from ats_cinepilot.map.graph import RoadGraph


def extract_curated_corridor_graph(
    graph: RoadGraph,
    *,
    corridor_name: str,
    edge_sequence: list[str] | tuple[str, ...],
    graph_source: str,
    alignment_mode: str,
    source_cache_path: str = "",
) -> RoadGraph:
    ordered_edges = [str(edge_id) for edge_id in edge_sequence]
    if not ordered_edges:
        raise ValueError("edge_sequence must not be empty")

    missing = [edge_id for edge_id in ordered_edges if edge_id not in graph.edges]
    if missing:
        raise ValueError(f"edge_sequence contains unknown edges: {missing}")

    for previous_edge_id, current_edge_id in zip(ordered_edges[:-1], ordered_edges[1:]):
        previous = graph.edges[previous_edge_id]
        current = graph.edges[current_edge_id]
        if previous.end_node_id != current.start_node_id:
            raise ValueError("edge_sequence must be connected in forward order")

    required_node_ids: set[str] = set()
    selected_edges = {}
    for edge_id in ordered_edges:
        edge = graph.edges[edge_id]
        selected_edges[edge_id] = replace(edge, metadata=dict(edge.metadata))
        required_node_ids.add(edge.start_node_id)
        required_node_ids.add(edge.end_node_id)

    selected_nodes = {
        node_id: graph.nodes[node_id]
        for node_id in required_node_ids
    }

    metadata = {
        "graph_source": graph_source,
        "alignment_mode": alignment_mode,
        "graph_kind": "curated_demo_corridor",
        "corridor_name": corridor_name,
        "approved_edge_sequence": ordered_edges,
        "source_graph_source": graph.metadata.get("graph_source"),
        "source_alignment_mode": graph.metadata.get("alignment_mode"),
        "source_export_toolchain": graph.metadata.get("export_toolchain"),
        "source_cache_path": source_cache_path,
        "exported_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    for key in (
        "source_format",
        "crop_center_x_m",
        "crop_center_z_m",
        "crop_radius_m",
        "focus_center_x_m",
        "focus_center_z_m",
        "focus_radius_m",
        "source_game_dir",
        "source_parser_dir",
        "source_input",
    ):
        if key in graph.metadata:
            metadata[key] = graph.metadata[key]

    return RoadGraph(nodes=selected_nodes, edges=selected_edges, metadata=metadata)


def normalize_cache_path(path: str | Path) -> str:
    return str(Path(path))
