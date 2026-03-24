from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from ats_cinepilot.bridge.scs_telemetry import (
    HttpJsonTelemetrySource,
    JsonTelemetryConfig,
    ReplayTelemetrySource,
    SharedMemoryV2Config,
    SharedMemoryV2TelemetrySource,
)
from ats_cinepilot.ops.config import cfg_get, resolve_config


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", action="append", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--seconds", type=float, default=20.0)
    parser.add_argument("--frames", type=int, default=0)
    parser.add_argument("--hz", type=float, default=10.0)
    parser.add_argument("--delay", type=float, default=0.0)
    args = parser.parse_args()

    cfg = resolve_config(args.config)
    source = _build_source(cfg)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    interval_s = 1.0 / max(args.hz, 1.0)
    max_frames = args.frames if args.frames > 0 else None

    source.connect()
    if args.delay > 0.0:
        print(f"recording starts in {args.delay:.1f}s")
        time.sleep(args.delay)

    written = 0
    started = time.monotonic()
    try:
        with output_path.open("w", encoding="utf-8") as handle:
            while True:
                if max_frames is not None and written >= max_frames:
                    break
                if max_frames is None and (time.monotonic() - started) >= args.seconds:
                    break

                frame = source.read()
                if frame is None:
                    print(f"frame[{written}]: no frame received")
                    break

                handle.write(json.dumps(frame.to_dict(), ensure_ascii=False) + "\n")
                handle.flush()
                written += 1

                if written == 1 or written % 10 == 0:
                    print(
                        f"frame={written} speed={frame.speed_mps:.3f} "
                        f"pose=({frame.pose.world_x:.2f}, {frame.pose.world_z:.2f}, yaw={frame.pose.yaw_rad:.3f})"
                    )

                sleep_s = started + written * interval_s - time.monotonic()
                if sleep_s > 0.0:
                    time.sleep(sleep_s)
    finally:
        if hasattr(source, "close"):
            source.close()

    print(f"saved {written} replay frames to {output_path}")


def _build_source(cfg: dict):
    source_name = cfg_get(cfg, "telemetry.source", "json_http")
    if source_name == "replay":
        return ReplayTelemetrySource(cfg_get(cfg, "logging.replay_path"))
    if source_name == "shared_memory_v2":
        return SharedMemoryV2TelemetrySource(
            SharedMemoryV2Config(
                mapping_name=cfg_get(cfg, "telemetry.shared_memory_name", "SCSTelemetrySharedv2_ats"),
                absolute_x_offset=cfg_get(cfg, "telemetry.absolute_x_offset"),
                absolute_y_offset=cfg_get(cfg, "telemetry.absolute_y_offset"),
                absolute_z_offset=cfg_get(cfg, "telemetry.absolute_z_offset"),
                absolute_value_format=cfg_get(cfg, "telemetry.absolute_value_format", "f64"),
                pose_frame_mode=cfg_get(cfg, "telemetry.pose_frame_mode", "anchored_local"),
                absolute_heading_min_distance_m=float(
                    cfg_get(cfg, "telemetry.absolute_heading_min_distance_m", 0.25)
                ),
                absolute_discontinuity_distance_m=float(
                    cfg_get(cfg, "telemetry.absolute_discontinuity_distance_m", 25.0)
                ),
            )
        )
    if source_name == "json_http":
        return HttpJsonTelemetrySource(
            JsonTelemetryConfig(
                endpoint=cfg_get(cfg, "telemetry.endpoint"),
                timeout_s=float(cfg_get(cfg, "telemetry.timeout_s", 0.2)),
                field_map=dict(cfg_get(cfg, "telemetry.field_map", {})),
            )
        )
    raise SystemExit(f"unsupported telemetry.source for replay recording: {source_name}")


if __name__ == "__main__":
    main()
