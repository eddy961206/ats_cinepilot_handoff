from __future__ import annotations

import json
from pathlib import Path

from ats_cinepilot.map.graph import Edge, Node, RoadGraph


def load_ts_map_graph(path: str | Path) -> RoadGraph:
    """
    ts-map export JSON을 internal graph로 변환하는 시작점.

    실제 exporter JSON 예시에 맞춰 로컬 codex가 필드명과 좌표계를 보정해야 한다.
    """
    payload = json.loads(Path(path).read_text(encoding="utf-8"))

    if "roads" in payload:
        return _from_roads(payload)

    if "edges" in payload and "nodes" in payload:
        return _from_generic(payload)

    raise ValueError("Unsupported ts-map export format")


def _from_roads(payload: dict) -> RoadGraph:
    nodes: dict[str, Node] = {}
    edges: dict[str, Edge] = {}
    for idx, road in enumerate(payload["roads"]):
        pts = road.get("points") or road.get("polyline") or []
        if len(pts) < 2:
            continue
        start_id = f"ts_n_{idx}_s"
        end_id = f"ts_n_{idx}_e"
        sx, sz = pts[0][:2]
        ex, ez = pts[-1][:2]
        nodes[start_id] = Node(node_id=start_id, x=float(sx), z=float(sz))
        nodes[end_id] = Node(node_id=end_id, x=float(ex), z=float(ez))
        edge_id = str(road.get("id", f"ts_e_{idx}"))
        edges[edge_id] = Edge(
            edge_id=edge_id,
            start_node_id=start_id,
            end_node_id=end_id,
            points=[(float(x), float(z)) for x, z, *_ in pts],
            speed_limit_mps=float(road["speed_limit_mps"]) if road.get("speed_limit_mps") else None,
            road_class=str(road.get("class", road.get("road_class", "unknown"))),
            metadata=road,
        )
    return RoadGraph(nodes=nodes, edges=edges)


def _from_generic(payload: dict) -> RoadGraph:
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
