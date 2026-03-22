from __future__ import annotations

import json
from pathlib import Path

from ats_cinepilot.map.graph import Edge, Node, RoadGraph


def load_trucksim_graph(path: str | Path) -> RoadGraph:
    """
    truckermudgeon/maps exporter JSON을 internal graph로 변환하는 시작점.

    실제 exporter 스키마가 프로젝트 버전에 따라 다를 수 있으니
    로컬 codex가 이 함수에서 실제 필드명을 맞춰야 한다.
    """
    payload = json.loads(Path(path).read_text(encoding="utf-8"))

    if "nodes" in payload and "edges" in payload:
        return _from_generic_nodes_edges(payload)

    if "features" in payload:
        return _from_geojson_like(payload)

    raise ValueError(
        "Unsupported trucksim maps export format. "
        "Inspect the exporter output and adapt this parser."
    )


def _from_generic_nodes_edges(payload: dict) -> RoadGraph:
    nodes = {
        str(n["id"]): Node(node_id=str(n["id"]), x=float(n["x"]), z=float(n["z"]))
        for n in payload["nodes"]
    }
    edges = {
        str(e["id"]): Edge(
            edge_id=str(e["id"]),
            start_node_id=str(e["start"]),
            end_node_id=str(e["end"]),
            points=[(float(x), float(z)) for x, z in e["points"]],
            speed_limit_mps=float(e["speed_limit_mps"]) if e.get("speed_limit_mps") else None,
            road_class=e.get("road_class", "unknown"),
            metadata=e,
        )
        for e in payload["edges"]
    }
    return RoadGraph(nodes=nodes, edges=edges)


def _from_geojson_like(payload: dict) -> RoadGraph:
    nodes: dict[str, Node] = {}
    edges: dict[str, Edge] = {}
    for idx, feat in enumerate(payload["features"]):
        geom = feat.get("geometry", {})
        if geom.get("type") != "LineString":
            continue
        coords = geom.get("coordinates", [])
        if len(coords) < 2:
            continue
        start_id = f"n_{idx}_s"
        end_id = f"n_{idx}_e"
        sx, sz = coords[0][:2]
        ex, ez = coords[-1][:2]
        nodes[start_id] = Node(node_id=start_id, x=float(sx), z=float(sz))
        nodes[end_id] = Node(node_id=end_id, x=float(ex), z=float(ez))
        props = feat.get("properties", {})
        edge_id = str(props.get("id", f"e_{idx}"))
        edges[edge_id] = Edge(
            edge_id=edge_id,
            start_node_id=start_id,
            end_node_id=end_id,
            points=[(float(x), float(z)) for x, z, *_ in coords],
            road_class=props.get("road_class", "unknown"),
            metadata=props,
        )
    return RoadGraph(nodes=nodes, edges=edges)
