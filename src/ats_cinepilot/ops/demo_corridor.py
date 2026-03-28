from __future__ import annotations

import math
from dataclasses import dataclass, replace
from pathlib import Path

from ats_cinepilot.map.cache import load_graph_cache
from ats_cinepilot.map.graph import Edge, Node, RoadGraph
from ats_cinepilot.ops.config import load_yaml

CURATED_CONNECT_GAP_TOLERANCE_M = 1.0


@dataclass(slots=True)
class CorridorEdgeSpec:
    edge_id: str
    source_edge_id: str
    source_travel_direction: str
    start_world_x: float
    start_world_z: float
    end_world_x: float
    end_world_z: float


@dataclass(slots=True)
class DemoCorridorContract:
    contract_path: Path
    corridor_name: str
    source_cache_path: str
    graph_cache_path: str
    graph_source: str
    alignment_mode: str
    start_edge_id: str
    end_edge_id: str
    ordered_edges: tuple[CorridorEdgeSpec, ...]
    translation_world_x_m: float
    translation_world_z_m: float
    start_progress_min_m: float | None
    start_progress_max_m: float | None
    completion_max_progress_m: float | None
    max_speed_mps: float
    min_match_confidence: float
    min_route_confidence: float
    max_cross_track_error_m: float
    max_heading_error_deg: float
    max_nearest_edge_distance_m: float
    max_graph_candidate_count: int


@dataclass(slots=True)
class CorridorProjection:
    spec_index: int
    spec: CorridorEdgeSpec
    progress_m: float
    distance_m: float
    projected_world_x: float
    projected_world_z: float
    translation_world_x_m: float
    translation_world_z_m: float


def load_demo_corridor_contract(path: str | Path) -> DemoCorridorContract:
    resolved = Path(path).resolve()
    payload = load_yaml(resolved)
    corridor = dict(payload.get("corridor", {}))
    demo = dict(payload.get("demo", {}))

    ordered_edges = tuple(
        CorridorEdgeSpec(
            edge_id=str(row["edge_id"]),
            source_edge_id=str(row["source_edge_id"]),
            source_travel_direction=str(row.get("source_travel_direction", "forward")),
            start_world_x=float(row["start_world_x"]),
            start_world_z=float(row["start_world_z"]),
            end_world_x=float(row["end_world_x"]),
            end_world_z=float(row["end_world_z"]),
        )
        for row in corridor.get("ordered_edges", [])
    )

    return DemoCorridorContract(
        contract_path=resolved,
        corridor_name=str(corridor["name"]),
        source_cache_path=str(corridor["source_cache_path"]),
        graph_cache_path=str(corridor["graph_cache_path"]),
        graph_source=str(corridor["graph_source"]),
        alignment_mode=str(corridor["alignment_mode"]),
        start_edge_id=str(corridor["start_edge_id"]),
        end_edge_id=str(corridor["end_edge_id"]),
        ordered_edges=ordered_edges,
        translation_world_x_m=float(corridor.get("translation_world_x_m", 0.0)),
        translation_world_z_m=float(corridor.get("translation_world_z_m", 0.0)),
        start_progress_min_m=_maybe_float(demo.get("start_progress_min_m")),
        start_progress_max_m=_maybe_float(
            demo.get("start_progress_max_m", demo.get("start_edge_max_progress_m"))
        ),
        completion_max_progress_m=_maybe_float(demo.get("completion_max_progress_m")),
        max_speed_mps=float(demo["max_speed_mps"]),
        min_match_confidence=float(demo["min_match_confidence"]),
        min_route_confidence=float(demo["min_route_confidence"]),
        max_cross_track_error_m=float(demo["max_cross_track_error_m"]),
        max_heading_error_deg=float(demo["max_heading_error_deg"]),
        max_nearest_edge_distance_m=float(demo["max_nearest_edge_distance_m"]),
        max_graph_candidate_count=int(demo["max_graph_candidate_count"]),
    )


def build_curated_corridor_graph(contract: DemoCorridorContract) -> RoadGraph:
    source_graph = load_graph_cache(contract.source_cache_path)
    nodes: dict[str, Node] = {}
    edges: dict[str, Edge] = {}
    previous_end_node_id: str | None = None
    previous_end_point: tuple[float, float] | None = None

    for index, spec in enumerate(contract.ordered_edges, start=1):
        source_edge = source_graph.edges[spec.source_edge_id]
        raw_points = source_graph.edge_points(spec.source_edge_id, spec.source_travel_direction)
        points = [
            (
                x + contract.translation_world_x_m,
                z + contract.translation_world_z_m,
            )
            for x, z in raw_points
        ]
        if len(points) < 2:
            raise ValueError(f"source edge has too few points: {spec.source_edge_id}")

        start_point = points[0]
        end_point = points[-1]
        if previous_end_point is not None:
            gap_m = (
                (previous_end_point[0] - start_point[0]) ** 2
                + (previous_end_point[1] - start_point[1]) ** 2
            ) ** 0.5
            if gap_m > CURATED_CONNECT_GAP_TOLERANCE_M:
                raise ValueError(
                    "corridor edge sequence is not contiguous: "
                    f"{contract.ordered_edges[index - 2].edge_id} -> {spec.edge_id}"
                )
            start_point = previous_end_point
            points = [start_point, *points[1:]]

        start_node_id = previous_end_node_id or f"n{index - 1}"
        end_node_id = f"n{index}"
        nodes.setdefault(start_node_id, Node(start_node_id, start_point[0], start_point[1]))
        nodes[end_node_id] = Node(end_node_id, end_point[0], end_point[1])
        edges[spec.edge_id] = Edge(
            edge_id=spec.edge_id,
            start_node_id=start_node_id,
            end_node_id=end_node_id,
            points=points,
            speed_limit_mps=source_edge.speed_limit_mps,
            road_class=source_edge.road_class,
            metadata={
                **dict(source_edge.metadata),
                "source_edge_id": spec.source_edge_id,
                "source_travel_direction": spec.source_travel_direction,
                "curated_corridor_name": contract.corridor_name,
            },
        )
        previous_end_node_id = end_node_id
        previous_end_point = end_point

    return RoadGraph(
        nodes=nodes,
        edges=edges,
        metadata={
            "graph_source": contract.graph_source,
            "alignment_mode": contract.alignment_mode,
            "graph_kind": "curated_demo",
            "corridor_name": contract.corridor_name,
            "source_cache_path": contract.source_cache_path,
            "contract_path": str(contract.contract_path),
            "translation_world_x_m": contract.translation_world_x_m,
            "translation_world_z_m": contract.translation_world_z_m,
        },
    )


def fit_contract_to_live_pose(
    contract: DemoCorridorContract,
    *,
    world_x: float,
    world_z: float,
    graph_cache_path: str | None = None,
    corridor_name: str | None = None,
    start_progress_backtrack_m: float = 12.0,
    start_progress_ahead_m: float = 25.0,
    completion_margin_m: float = 15.0,
) -> tuple[DemoCorridorContract, CorridorProjection]:
    source_graph = load_graph_cache(contract.source_cache_path)
    projection = nearest_corridor_projection(
        source_graph,
        contract.ordered_edges,
        world_x=world_x,
        world_z=world_z,
    )
    trimmed_edges = contract.ordered_edges[projection.spec_index :]
    start_edge_id = trimmed_edges[0].edge_id
    last_edge_points = source_graph.edge_points(
        trimmed_edges[-1].source_edge_id,
        trimmed_edges[-1].source_travel_direction,
    )
    last_edge_length_m = _polyline_length(last_edge_points)
    completion_max_progress_m = max(5.0, last_edge_length_m - completion_margin_m)
    fitted = replace(
        contract,
        corridor_name=corridor_name or contract.corridor_name,
        graph_cache_path=graph_cache_path or contract.graph_cache_path,
        start_edge_id=start_edge_id,
        end_edge_id=trimmed_edges[-1].edge_id,
        ordered_edges=tuple(
            _translated_edge_spec(
                spec,
                projection.translation_world_x_m,
                projection.translation_world_z_m,
            )
            for spec in trimmed_edges
        ),
        translation_world_x_m=projection.translation_world_x_m,
        translation_world_z_m=projection.translation_world_z_m,
        start_progress_min_m=max(0.0, projection.progress_m - start_progress_backtrack_m),
        start_progress_max_m=projection.progress_m + start_progress_ahead_m,
        completion_max_progress_m=completion_max_progress_m,
    )
    return fitted, projection


def nearest_corridor_projection(
    source_graph: RoadGraph,
    ordered_edges: tuple[CorridorEdgeSpec, ...],
    *,
    world_x: float,
    world_z: float,
) -> CorridorProjection:
    best: CorridorProjection | None = None
    for index, spec in enumerate(ordered_edges):
        points = source_graph.edge_points(spec.source_edge_id, spec.source_travel_direction)
        progress_m, distance_m, projected_world_x, projected_world_z = _project_onto_polyline(
            world_x,
            world_z,
            points,
        )
        candidate = CorridorProjection(
            spec_index=index,
            spec=spec,
            progress_m=progress_m,
            distance_m=distance_m,
            projected_world_x=projected_world_x,
            projected_world_z=projected_world_z,
            translation_world_x_m=world_x - projected_world_x,
            translation_world_z_m=world_z - projected_world_z,
        )
        if best is None or candidate.distance_m < best.distance_m:
            best = candidate
    if best is None:
        raise ValueError("ordered_edges must not be empty")
    return best


def _translated_edge_spec(
    spec: CorridorEdgeSpec,
    translation_world_x_m: float,
    translation_world_z_m: float,
) -> CorridorEdgeSpec:
    return CorridorEdgeSpec(
        edge_id=spec.edge_id,
        source_edge_id=spec.source_edge_id,
        source_travel_direction=spec.source_travel_direction,
        start_world_x=spec.start_world_x + translation_world_x_m,
        start_world_z=spec.start_world_z + translation_world_z_m,
        end_world_x=spec.end_world_x + translation_world_x_m,
        end_world_z=spec.end_world_z + translation_world_z_m,
    )


def _project_onto_polyline(
    world_x: float,
    world_z: float,
    points: list[tuple[float, float]],
) -> tuple[float, float, float, float]:
    if len(points) < 2:
        raise ValueError("points must contain at least two items")

    best_distance = float("inf")
    best_progress = 0.0
    best_projected_x = points[0][0]
    best_projected_z = points[0][1]
    traversed = 0.0
    for (ax, az), (bx, bz) in zip(points[:-1], points[1:]):
        seg_dx = bx - ax
        seg_dz = bz - az
        seg_len_sq = seg_dx * seg_dx + seg_dz * seg_dz
        if seg_len_sq <= 1e-9:
            continue
        t = ((world_x - ax) * seg_dx + (world_z - az) * seg_dz) / seg_len_sq
        t = max(0.0, min(1.0, t))
        projected_x = ax + seg_dx * t
        projected_z = az + seg_dz * t
        distance = math.dist((world_x, world_z), (projected_x, projected_z))
        if distance < best_distance:
            best_distance = distance
            seg_len = math.sqrt(seg_len_sq)
            best_progress = traversed + seg_len * t
            best_projected_x = projected_x
            best_projected_z = projected_z
        traversed += math.sqrt(seg_len_sq)
    return best_progress, best_distance, best_projected_x, best_projected_z


def _polyline_length(points: list[tuple[float, float]]) -> float:
    total = 0.0
    for a, b in zip(points[:-1], points[1:]):
        total += math.dist(a, b)
    return total


def _maybe_float(value: object) -> float | None:
    if value is None or value == "":
        return None
    return float(value)
