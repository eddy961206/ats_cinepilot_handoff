from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from .graph import Edge, Node, RoadGraph


def load_graph_cache(path: str | Path) -> RoadGraph:
    p = Path(path)
    payload = json.loads(p.read_text(encoding="utf-8"))
    nodes = {
        str(row["node_id"]): Node(
            node_id=str(row["node_id"]),
            x=float(row["x"]),
            z=float(row["z"]),
        )
        for row in payload["nodes"]
    }
    edges = {
        str(row["edge_id"]): Edge(
            edge_id=str(row["edge_id"]),
            start_node_id=str(row["start_node_id"]),
            end_node_id=str(row["end_node_id"]),
            points=[(float(x), float(z)) for x, z in row["points"]],
            speed_limit_mps=_opt_float(row.get("speed_limit_mps")),
            road_class=row.get("road_class", "unknown"),
            metadata=row.get("metadata", {}),
        )
        for row in payload["edges"]
    }
    return RoadGraph(nodes=nodes, edges=edges, metadata=payload.get("metadata", {}))


def save_graph_cache(graph: RoadGraph, path: str | Path, *, indent: int | None = 2) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "metadata": graph.metadata,
        "nodes": [
            {"node_id": n.node_id, "x": n.x, "z": n.z}
            for n in graph.nodes.values()
        ],
        "edges": [
            {
                "edge_id": e.edge_id,
                "start_node_id": e.start_node_id,
                "end_node_id": e.end_node_id,
                "points": e.points,
                "speed_limit_mps": e.speed_limit_mps,
                "road_class": e.road_class,
                "metadata": e.metadata,
            }
            for e in graph.edges.values()
        ],
    }
    p.write_text(
        json.dumps(payload, ensure_ascii=False, indent=indent, separators=None if indent is not None else (",", ":")),
        encoding="utf-8",
    )


def extract_ordered_corridor_graph(
    source_graph: RoadGraph,
    edge_sequence: Iterable[dict[str, str]],
    *,
    graph_source: str,
    alignment_mode: str,
    corridor_name: str,
) -> RoadGraph:
    oriented_nodes: dict[str, Node] = {}
    oriented_edges: dict[str, Edge] = {}
    selected_edge_sequence: list[dict[str, str]] = []
    previous_end_node_id: str | None = None

    for index, item in enumerate(edge_sequence):
        source_edge_id = str(item["edge_id"])
        travel_direction = str(item.get("travel_direction", "forward"))
        source_edge = source_graph.edges[source_edge_id]
        oriented_edge = _orient_edge(source_edge, travel_direction=travel_direction)
        if previous_end_node_id is not None and oriented_edge.start_node_id != previous_end_node_id:
            raise ValueError(
                "edge sequence is not contiguous: "
                f"{selected_edge_sequence[-1]['edge_id']} -> {source_edge_id}"
            )
        previous_end_node_id = oriented_edge.end_node_id
        oriented_edge.metadata = {
            **dict(source_edge.metadata),
            "source_edge_id": source_edge_id,
            "travel_direction": travel_direction,
            "corridor_index": index,
        }
        selected_edge_sequence.append(
            {
                "edge_id": oriented_edge.edge_id,
                "source_edge_id": source_edge_id,
                "travel_direction": travel_direction,
            }
        )
        for node_id, (x, z) in (
            (oriented_edge.start_node_id, oriented_edge.points[0]),
            (oriented_edge.end_node_id, oriented_edge.points[-1]),
        ):
            oriented_nodes[node_id] = Node(node_id=node_id, x=float(x), z=float(z))
        oriented_edges[oriented_edge.edge_id] = oriented_edge

    metadata = dict(source_graph.metadata)
    metadata.update(
        {
            "graph_source": graph_source,
            "alignment_mode": alignment_mode,
            "corridor_name": corridor_name,
            "selected_edge_sequence": selected_edge_sequence,
            "source_graph_source": source_graph.metadata.get("graph_source"),
            "source_alignment_mode": source_graph.metadata.get("alignment_mode"),
        }
    )
    return RoadGraph(nodes=oriented_nodes, edges=oriented_edges, metadata=metadata)


def _opt_float(value):
    if value is None or value == "":
        return None
    return float(value)


def _orient_edge(edge: Edge, *, travel_direction: str) -> Edge:
    if travel_direction not in {"forward", "reverse"}:
        raise ValueError(f"unsupported travel_direction: {travel_direction}")
    if travel_direction == "forward":
        return Edge(
            edge_id=edge.edge_id,
            start_node_id=edge.start_node_id,
            end_node_id=edge.end_node_id,
            points=list(edge.points),
            speed_limit_mps=edge.speed_limit_mps,
            road_class=edge.road_class,
            metadata=dict(edge.metadata),
        )
    return Edge(
        edge_id=f"{edge.edge_id}__reverse",
        start_node_id=edge.end_node_id,
        end_node_id=edge.start_node_id,
        points=list(reversed(edge.points)),
        speed_limit_mps=edge.speed_limit_mps,
        road_class=edge.road_class,
        metadata=dict(edge.metadata),
    )
