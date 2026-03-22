from __future__ import annotations

import json
from pathlib import Path

import requests

from ats_cinepilot.map.graph import Edge, Node, RoadGraph
from ats_cinepilot.map.projections import wgs84_to_ats_coords
from ats_cinepilot.map.spatial_index import point_segment_distance


def load_trucksim_graph(path: str | Path) -> RoadGraph:
    """
    truckermudgeon/maps exporter JSON을 internal graph로 변환하는 시작점.

    실제 exporter 스키마가 프로젝트 버전에 따라 다를 수 있으니
    로컬 codex가 이 함수에서 실제 필드명을 맞춰야 한다.
    """
    payload = _load_payload(path)

    if "demoGraph" in payload and "demoNodes" in payload:
        return _from_demo_graph(payload)

    if "nodes" in payload and "edges" in payload:
        return _from_generic_nodes_edges(payload)

    if "features" in payload:
        return _from_geojson_like(payload)

    raise ValueError(
        "Unsupported trucksim maps export format. "
        "Inspect the exporter output and adapt this parser."
    )


def _load_payload(path: str | Path) -> dict:
    path_str = str(path)
    if path_str.startswith(("http://", "https://")):
        response = requests.get(path_str, timeout=120)
        response.raise_for_status()
        return response.json()
    return json.loads(Path(path).read_text(encoding="utf-8"))


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
    return RoadGraph(nodes=nodes, edges=edges, metadata={"source_format": "trucksim_generic"})


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
    return RoadGraph(nodes=nodes, edges=edges, metadata={"source_format": "trucksim_geojson"})


def _from_demo_graph(payload: dict) -> RoadGraph:
    raw_nodes = payload.get("demoNodes", [])
    raw_graph = payload.get("demoGraph", [])

    nodes: dict[str, Node] = {}
    for node_id, coords in raw_nodes:
        lon, lat = coords
        x_m, z_m = wgs84_to_ats_coords(float(lon), float(lat))
        nodes[str(node_id)] = Node(
            node_id=str(node_id),
            x=float(x_m),
            z=float(z_m),
        )

    edges: dict[str, Edge] = {}
    for node_id, neighbors in raw_graph:
        start_id = str(node_id)
        start_node = nodes[start_id]
        for direction_key in ("f", "b"):
            for idx, neighbor in enumerate(neighbors.get(direction_key, []) or []):
                end_id = str(neighbor["n"])
                end_node = nodes[end_id]
                distance_m = float(neighbor.get("l", 0.0) or 0.0)
                duration_s = float(neighbor.get("m", 0.0) or 0.0)
                speed_limit_mps = distance_m / duration_s if duration_s > 0.0 else None
                edge_id = f"{start_id}__{end_id}__{direction_key}__{idx}"
                edges[edge_id] = Edge(
                    edge_id=edge_id,
                    start_node_id=start_id,
                    end_node_id=end_id,
                    points=[(start_node.x, start_node.z), (end_node.x, end_node.z)],
                    speed_limit_mps=speed_limit_mps,
                    road_class="trucksim_demo_graph",
                    metadata={
                        "dlc_guard": neighbor.get("g"),
                        "direction": neighbor.get("d", direction_key),
                        "one_lane": bool(neighbor.get("o", False)),
                        "source_neighbor_length_m": distance_m,
                        "source_neighbor_duration_s": duration_s,
                    },
                )

    return RoadGraph(
        nodes=nodes,
        edges=edges,
        metadata={
            "source_format": "trucksim_demo_graph",
            "source_node_count": len(nodes),
            "source_edge_count": len(edges),
        },
    )


def crop_graph_to_radius(
    graph: RoadGraph,
    *,
    center_x_m: float,
    center_z_m: float,
    radius_m: float,
) -> RoadGraph:
    kept_edges: dict[str, Edge] = {}
    kept_node_ids: set[str] = set()

    for edge_id, edge in graph.edges.items():
        should_keep = False
        for (ax, az), (bx, bz) in zip(edge.points[:-1], edge.points[1:]):
            dist_m, _ = point_segment_distance(center_x_m, center_z_m, ax, az, bx, bz)
            if dist_m <= radius_m:
                should_keep = True
                break
        if not should_keep:
            continue
        kept_edges[edge_id] = edge
        kept_node_ids.add(edge.start_node_id)
        kept_node_ids.add(edge.end_node_id)

    kept_nodes = {
        node_id: node
        for node_id, node in graph.nodes.items()
        if node_id in kept_node_ids
    }

    return RoadGraph(
        nodes=kept_nodes,
        edges=kept_edges,
        metadata={
            **graph.metadata,
            "crop_center_x_m": center_x_m,
            "crop_center_z_m": center_z_m,
            "crop_radius_m": radius_m,
            "cropped_node_count": len(kept_nodes),
            "cropped_edge_count": len(kept_edges),
        },
    )
