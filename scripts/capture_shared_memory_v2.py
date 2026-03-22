from __future__ import annotations

import argparse
import base64
import json
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from ats_cinepilot.bridge.scs_telemetry import SharedMemoryV2Config, SharedMemoryV2TelemetrySource
from ats_cinepilot.ops.config import cfg_get, resolve_config


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", action="append", required=True)
    parser.add_argument("--seconds", type=float, default=12.0)
    parser.add_argument("--hz", type=float, default=10.0)
    parser.add_argument("--label", default="capture")
    parser.add_argument("--note", default="")
    parser.add_argument("--output", default="")
    parser.add_argument("--delay", type=float, default=0.0)
    args = parser.parse_args()

    cfg = resolve_config(args.config)
    if cfg_get(cfg, "telemetry.source") != "shared_memory_v2":
        raise SystemExit("capture_shared_memory_v2.py requires telemetry.source=shared_memory_v2")

    source = SharedMemoryV2TelemetrySource(_build_shared_memory_v2_config(cfg))
    source.connect()
    interval_s = 1.0 / max(args.hz, 1.0)
    output_path = Path(args.output) if args.output else _default_output_path(args.label)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if args.delay > 0.0:
        print(f"capture starts in {args.delay:.1f}s")
        time.sleep(args.delay)

    with output_path.open("w", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                {
                    "type": "capture_metadata",
                    "captured_at_utc": datetime.now(timezone.utc).isoformat(),
                    "label": args.label,
                    "note": args.note,
                    "seconds": args.seconds,
                    "hz": args.hz,
                    "mapping_name": source.config.mapping_name,
                    "absolute_x_offset": source.config.absolute_x_offset,
                    "absolute_y_offset": source.config.absolute_y_offset,
                    "absolute_z_offset": source.config.absolute_z_offset,
                    "absolute_value_format": source.config.absolute_value_format,
                    "pose_frame_mode": source.config.pose_frame_mode,
                    "absolute_heading_min_distance_m": source.config.absolute_heading_min_distance_m,
                    "absolute_discontinuity_distance_m": source.config.absolute_discontinuity_distance_m,
                },
                ensure_ascii=False,
            )
            + "\n"
        )

        started = time.monotonic()
        sample_index = 0
        try:
            while True:
                now = time.monotonic()
                if now - started >= args.seconds:
                    break
                raw = source.read_raw()
                frame = source.decoder.decode(raw, mono_time_s=now)
                state = source.last_state
                handle.write(
                    json.dumps(
                        {
                            "type": "sample",
                            "sample_index": sample_index,
                            "captured_at_utc": datetime.now(timezone.utc).isoformat(),
                            "label": args.label,
                            "note": args.note,
                            "raw_b64": base64.b64encode(raw).decode("ascii"),
                            "frame": frame.to_dict(),
                            "state": asdict(state) if state is not None else None,
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )
                if sample_index % 10 == 0 and state is not None:
                    print(
                        f"sample={sample_index} speed={frame.speed_mps:.3f} "
                        f"pose=({frame.pose.world_x:.2f}, {frame.pose.world_z:.2f}, yaw={frame.pose.yaw_rad:.3f}) "
                        f"pose_source={state.pose_source} heading_source={state.heading_source}"
                    )
                sample_index += 1
                sleep_s = started + sample_index * interval_s - time.monotonic()
                if sleep_s > 0.0:
                    time.sleep(sleep_s)
        finally:
            source.close()

    print(f"saved {sample_index} samples to {output_path}")


def _build_shared_memory_v2_config(cfg: dict) -> SharedMemoryV2Config:
    return SharedMemoryV2Config(
        mapping_name=cfg_get(cfg, "telemetry.shared_memory_name", "SCSTelemetrySharedv2_ats"),
        absolute_x_offset=cfg_get(cfg, "telemetry.absolute_x_offset"),
        absolute_y_offset=cfg_get(cfg, "telemetry.absolute_y_offset"),
        absolute_z_offset=cfg_get(cfg, "telemetry.absolute_z_offset"),
        absolute_value_format=cfg_get(cfg, "telemetry.absolute_value_format", "f64"),
        pose_frame_mode=cfg_get(cfg, "telemetry.pose_frame_mode", "anchored_local"),
        absolute_heading_min_distance_m=float(cfg_get(cfg, "telemetry.absolute_heading_min_distance_m", 0.25)),
        absolute_discontinuity_distance_m=float(cfg_get(cfg, "telemetry.absolute_discontinuity_distance_m", 25.0)),
    )


def _default_output_path(label: str) -> Path:
    safe_label = "".join(ch if ch.isalnum() or ch in {"_", "-"} else "_" for ch in label).strip("_") or "capture"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return Path("data") / "captures" / "shared_memory_v2" / f"{stamp}_{safe_label}.jsonl"


if __name__ == "__main__":
    main()
