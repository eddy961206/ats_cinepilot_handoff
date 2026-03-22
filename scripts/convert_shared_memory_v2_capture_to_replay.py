from __future__ import annotations

import argparse
import base64
import json
from pathlib import Path

from ats_cinepilot.bridge.scs_telemetry import SharedMemoryV2Config, SharedMemoryV2Decoder
from ats_cinepilot.ops.config import cfg_get, resolve_config


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="capture_shared_memory_v2.py output jsonl")
    parser.add_argument("--output", required=True, help="Replay jsonl output path")
    parser.add_argument("--config", action="append", required=True)
    parser.add_argument(
        "--pose-frame-mode",
        choices=["anchored_local", "world_absolute"],
        required=True,
    )
    args = parser.parse_args()

    cfg = resolve_config(args.config)
    decoder = SharedMemoryV2Decoder(_build_decoder_config(cfg, args.pose_frame_mode))
    input_path = Path(args.input)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    written = 0
    with input_path.open("r", encoding="utf-8") as src, output_path.open("w", encoding="utf-8") as dst:
        for line in src:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("type") != "sample":
                continue
            raw = base64.b64decode(row["raw_b64"])
            captured_frame = row.get("frame", {})
            mono_time_s = float(captured_frame.get("mono_time_s", row.get("sample_index", written)))
            frame = decoder.decode(raw, mono_time_s=mono_time_s)
            dst.write(json.dumps(frame.to_dict(), ensure_ascii=False) + "\n")
            written += 1

    print(f"converted {written} frames from {input_path} -> {output_path}")


def _build_decoder_config(cfg: dict, pose_frame_mode: str) -> SharedMemoryV2Config:
    return SharedMemoryV2Config(
        mapping_name=cfg_get(cfg, "telemetry.shared_memory_name", "SCSTelemetrySharedv2_ats"),
        absolute_x_offset=cfg_get(cfg, "telemetry.absolute_x_offset"),
        absolute_y_offset=cfg_get(cfg, "telemetry.absolute_y_offset"),
        absolute_z_offset=cfg_get(cfg, "telemetry.absolute_z_offset"),
        absolute_value_format=cfg_get(cfg, "telemetry.absolute_value_format", "f64"),
        pose_frame_mode=pose_frame_mode,
        absolute_heading_min_distance_m=float(cfg_get(cfg, "telemetry.absolute_heading_min_distance_m", 0.25)),
        absolute_discontinuity_distance_m=float(cfg_get(cfg, "telemetry.absolute_discontinuity_distance_m", 25.0)),
    )


if __name__ == "__main__":
    main()
