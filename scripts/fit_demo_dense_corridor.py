from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from ats_cinepilot.bridge.scs_telemetry import SharedMemoryV2Config, SharedMemoryV2TelemetrySource
from ats_cinepilot.ops.config import cfg_get, resolve_config
from ats_cinepilot.ops.demo_corridor import fit_contract_to_live_pose, load_demo_corridor_contract


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", action="append", required=True)
    parser.add_argument("--contract", default="configs/corridors/demo_dense_curated_corridor.yaml")
    parser.add_argument(
        "--output-contract",
        default="data/runtime/demo_dense_curated_corridor.runtime.yaml",
    )
    parser.add_argument(
        "--output-graph",
        default="data/maps/cache/demo_dense_curated_corridor.runtime.json",
    )
    parser.add_argument("--frames", type=int, default=3)
    parser.add_argument("--max-fit-distance-m", type=float, default=25.0)
    parser.add_argument("--start-backtrack-m", type=float, default=8.0)
    parser.add_argument("--start-ahead-m", type=float, default=20.0)
    parser.add_argument("--completion-margin-m", type=float, default=15.0)
    args = parser.parse_args()

    cfg = resolve_config(args.config)
    if cfg_get(cfg, "telemetry.source") != "shared_memory_v2":
        raise SystemExit("fit_demo_dense_corridor.py requires telemetry.source=shared_memory_v2")

    frame = _read_live_frame(cfg, frames=max(1, args.frames))
    contract = load_demo_corridor_contract(args.contract)
    fitted, projection = fit_contract_to_live_pose(
        contract,
        world_x=frame.pose.world_x,
        world_z=frame.pose.world_z,
        graph_cache_path=args.output_graph,
        corridor_name=f"{contract.corridor_name}_runtime",
        start_progress_backtrack_m=args.start_backtrack_m,
        start_progress_ahead_m=args.start_ahead_m,
        completion_margin_m=args.completion_margin_m,
    )
    if projection.distance_m > args.max_fit_distance_m:
        raise SystemExit(
            "live pose is too far from the curated dense corridor source geometry: "
            f"{projection.distance_m:.3f}m > {args.max_fit_distance_m:.3f}m"
        )

    payload = {
        "corridor": {
            "name": fitted.corridor_name,
            "source_cache_path": fitted.source_cache_path,
            "graph_cache_path": fitted.graph_cache_path,
            "graph_source": fitted.graph_source,
            "alignment_mode": fitted.alignment_mode,
            "translation_world_x_m": fitted.translation_world_x_m,
            "translation_world_z_m": fitted.translation_world_z_m,
            "start_edge_id": fitted.start_edge_id,
            "end_edge_id": fitted.end_edge_id,
            "ordered_edges": [
                {
                    "edge_id": edge.edge_id,
                    "source_edge_id": edge.source_edge_id,
                    "source_travel_direction": edge.source_travel_direction,
                    "start_world_x": edge.start_world_x,
                    "start_world_z": edge.start_world_z,
                    "end_world_x": edge.end_world_x,
                    "end_world_z": edge.end_world_z,
                }
                for edge in fitted.ordered_edges
            ],
        },
        "map": {
            "cache_path": fitted.graph_cache_path,
            "source_name": fitted.graph_source,
            "alignment_mode": fitted.alignment_mode,
        },
        "demo": {
            "contract_path": args.output_contract,
            "corridor_name": fitted.corridor_name,
            "approved_graph_source": fitted.graph_source,
            "approved_alignment_mode": fitted.alignment_mode,
            "approved_edge_ids": [edge.edge_id for edge in fitted.ordered_edges],
            "approved_edge_sequence": [edge.edge_id for edge in fitted.ordered_edges],
            "start_edge_id": fitted.start_edge_id,
            "start_progress_min_m": fitted.start_progress_min_m,
            "start_progress_max_m": fitted.start_progress_max_m,
            "completion_edge_id": fitted.end_edge_id,
            "completion_max_progress_m": fitted.completion_max_progress_m,
            "allowed_travel_directions": list(cfg_get(cfg, "demo.allowed_travel_directions", ["forward"])),
            "allowed_direction_confidence_states": list(
                cfg_get(cfg, "demo.allowed_direction_confidence_states", ["confident"])
            ),
            "allowed_pose_sources": list(
                cfg_get(cfg, "demo.allowed_pose_sources", ["authoritative_absolute"])
            ),
            "allowed_heading_sources": list(
                cfg_get(
                    cfg,
                    "demo.allowed_heading_sources",
                    ["absolute_position_delta", "absolute_position_hold"],
                )
            ),
            "min_match_confidence": max(0.98, float(cfg_get(cfg, "demo.min_match_confidence", 0.98))),
            "min_route_confidence": max(0.67, float(cfg_get(cfg, "demo.min_route_confidence", 0.67))),
            "max_cross_track_error_m": min(0.45, float(cfg_get(cfg, "demo.max_cross_track_error_m", 0.45))),
            "max_heading_error_deg": float(cfg_get(cfg, "demo.max_heading_error_deg", 6.0)),
            "max_nearest_edge_distance_m": min(
                0.45, float(cfg_get(cfg, "demo.max_nearest_edge_distance_m", 0.45))
            ),
            "max_speed_mps": float(cfg_get(cfg, "demo.max_speed_mps", 2.5)),
            "max_graph_candidate_count": min(1, int(cfg_get(cfg, "demo.max_graph_candidate_count", 1))),
            "require_anchor_locked": bool(cfg_get(cfg, "demo.require_anchor_locked", True)),
            "require_no_discontinuity": bool(cfg_get(cfg, "demo.require_no_discontinuity", True)),
            "arm_consecutive_frames": int(cfg_get(cfg, "demo.arm_consecutive_frames", 10)),
            "bootstrap_max_speed_mps": max(1.0, float(cfg_get(cfg, "demo.bootstrap_max_speed_mps", 1.0))),
            "bootstrap_throttle": max(0.7, float(cfg_get(cfg, "demo.bootstrap_throttle", 1.0))),
            "bootstrap_min_match_confidence": max(
                0.60, float(cfg_get(cfg, "demo.bootstrap_min_match_confidence", 0.60))
            ),
            "bootstrap_max_cross_track_error_m": min(
                0.80, float(cfg_get(cfg, "demo.bootstrap_max_cross_track_error_m", 0.80))
            ),
            "bootstrap_max_nearest_edge_distance_m": min(
                0.80, float(cfg_get(cfg, "demo.bootstrap_max_nearest_edge_distance_m", 0.80))
            ),
            "allow_speed_cap_brake_assist": bool(
                cfg_get(cfg, "demo.allow_speed_cap_brake_assist", True)
            ),
        },
    }

    output_contract = Path(args.output_contract)
    output_contract.parent.mkdir(parents=True, exist_ok=True)
    output_contract.write_text(
        yaml.safe_dump(payload, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    print(f"saved runtime corridor overlay: {output_contract}")
    print(f"  live_pose=({frame.pose.world_x:.3f}, {frame.pose.world_z:.3f})")
    print(
        "  fitted_edge={edge} distance_m={distance:.3f} progress_m={progress:.3f}".format(
            edge=projection.spec.edge_id,
            distance=projection.distance_m,
            progress=projection.progress_m,
        )
    )
    print(
        "  translation_world=({dx:.3f}, {dz:.3f}) start_window=[{start_min:.3f}, {start_max:.3f}]".format(
            dx=fitted.translation_world_x_m,
            dz=fitted.translation_world_z_m,
            start_min=fitted.start_progress_min_m or 0.0,
            start_max=fitted.start_progress_max_m or 0.0,
        )
    )
    print(f"  graph_cache_path={fitted.graph_cache_path}")


def _read_live_frame(cfg: dict, *, frames: int):
    source = SharedMemoryV2TelemetrySource(
        SharedMemoryV2Config(
            mapping_name=cfg_get(cfg, "telemetry.shared_memory_name", "SCSTelemetrySharedv2_ats"),
            absolute_x_offset=cfg_get(cfg, "telemetry.absolute_x_offset"),
            absolute_y_offset=cfg_get(cfg, "telemetry.absolute_y_offset"),
            absolute_z_offset=cfg_get(cfg, "telemetry.absolute_z_offset"),
            absolute_value_format=cfg_get(cfg, "telemetry.absolute_value_format", "f64"),
            pose_frame_mode=cfg_get(cfg, "telemetry.pose_frame_mode", "world_absolute"),
            absolute_heading_min_distance_m=float(
                cfg_get(cfg, "telemetry.absolute_heading_min_distance_m", 0.25)
            ),
            absolute_discontinuity_distance_m=float(
                cfg_get(cfg, "telemetry.absolute_discontinuity_distance_m", 25.0)
            ),
        )
    )
    source.connect()
    try:
        frame = None
        for _ in range(frames):
            frame = source.read()
            if frame is None:
                raise SystemExit(f"failed to decode live telemetry: {source.last_error or 'unknown error'}")
        if frame is None:
            raise SystemExit("no live telemetry frame received")
        return frame
    finally:
        source.close()


if __name__ == "__main__":
    main()
