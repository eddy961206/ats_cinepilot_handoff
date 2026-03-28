from __future__ import annotations

import argparse

from ats_cinepilot.bridge.scs_telemetry import (
    HttpJsonTelemetrySource,
    JsonTelemetryConfig,
    ReplayTelemetrySource,
    SharedMemoryV2Config,
    SharedMemoryV2TelemetrySource,
)
from ats_cinepilot.map.adapters.trucksim_maps import crop_graph_to_radius, load_trucksim_graph
from ats_cinepilot.map.adapters.ts_map import load_ts_map_graph
from ats_cinepilot.map.cache import save_graph_cache
from ats_cinepilot.ops.config import cfg_get, resolve_config


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source",
        choices=["trucksim", "trucksim-demo", "trucksim-ats-geojson", "ts-map"],
        required=True,
    )
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--compact", action="store_true", help="Write compact JSON instead of indented JSON.")
    parser.add_argument("--crop-center-x", type=float)
    parser.add_argument("--crop-center-z", type=float)
    parser.add_argument("--crop-radius-m", type=float)
    parser.add_argument(
        "--center-from-config",
        action="append",
        default=[],
        help="Config path(s) used to read a live or replay telemetry frame for crop center.",
    )
    args = parser.parse_args()

    if args.source in {"trucksim", "trucksim-demo", "trucksim-ats-geojson"}:
        graph = load_trucksim_graph(args.input)
    else:
        graph = load_ts_map_graph(args.input)

    crop_center_x = args.crop_center_x
    crop_center_z = args.crop_center_z
    if args.center_from_config:
        crop_center_x, crop_center_z = read_center_from_config(args.center_from_config)

    if args.crop_radius_m is not None:
        if crop_center_x is None or crop_center_z is None:
            raise ValueError("--crop-radius-m requires either --crop-center-x/--crop-center-z or --center-from-config")
        graph = crop_graph_to_radius(
            graph,
            center_x_m=float(crop_center_x),
            center_z_m=float(crop_center_z),
            radius_m=float(args.crop_radius_m),
        )

    graph.metadata.update(
        {
            "graph_source": _graph_source_name(args.source),
            "alignment_mode": "ats_absolute_identity",
            "source_input": args.input,
        }
    )
    save_graph_cache(graph, args.output, indent=None if args.compact else 2)
    print(f"saved internal graph cache to {args.output}")


def _graph_source_name(source: str) -> str:
    if source in {"trucksim", "trucksim-demo"}:
        return "trucksim_demo_graph_region"
    if source == "trucksim-ats-geojson":
        return "trucksim_local_geojson_region"
    return source


def read_center_from_config(config_paths: list[str]) -> tuple[float, float]:
    cfg = resolve_config(config_paths)
    telemetry_source_name = cfg_get(cfg, "telemetry.source", "json_http")
    if telemetry_source_name == "shared_memory_v2":
        telemetry_source = SharedMemoryV2TelemetrySource(
            SharedMemoryV2Config(
                mapping_name=cfg_get(cfg, "telemetry.shared_memory_name", "SCSTelemetrySharedv2_ats"),
                absolute_x_offset=cfg_get(cfg, "telemetry.absolute_x_offset"),
                absolute_y_offset=cfg_get(cfg, "telemetry.absolute_y_offset"),
                absolute_z_offset=cfg_get(cfg, "telemetry.absolute_z_offset"),
                absolute_value_format=cfg_get(cfg, "telemetry.absolute_value_format", "f64"),
                pose_frame_mode="world_absolute",
                absolute_heading_min_distance_m=float(
                    cfg_get(cfg, "telemetry.absolute_heading_min_distance_m", 0.25)
                ),
                absolute_discontinuity_distance_m=float(
                    cfg_get(cfg, "telemetry.absolute_discontinuity_distance_m", 25.0)
                ),
            )
        )
    elif telemetry_source_name == "replay":
        telemetry_source = ReplayTelemetrySource(cfg_get(cfg, "logging.replay_path"))
    else:
        telemetry_source = HttpJsonTelemetrySource(
            JsonTelemetryConfig(
                endpoint=cfg_get(cfg, "telemetry.endpoint"),
                timeout_s=float(cfg_get(cfg, "telemetry.timeout_s", 0.2)),
                field_map=dict(cfg_get(cfg, "telemetry.field_map", {})),
            )
        )

    telemetry_source.connect()
    try:
        frame = telemetry_source.read()
        if frame is None:
            raise RuntimeError("telemetry source did not produce a frame for crop center")
        return frame.pose.world_x, frame.pose.world_z
    finally:
        if hasattr(telemetry_source, "close"):
            telemetry_source.close()


if __name__ == "__main__":
    main()
