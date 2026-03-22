from __future__ import annotations

import json
from pathlib import Path

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
    return RoadGraph(nodes=nodes, edges=edges)


def save_graph_cache(graph: RoadGraph, path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    payload = {
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
    p.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _opt_float(value):
    if value is None or value == "":
        return None
    return float(value)
