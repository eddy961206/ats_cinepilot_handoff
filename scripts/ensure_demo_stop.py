from __future__ import annotations

import argparse
import time

from ats_cinepilot.bridge.hybrid_controls import HybridControlConfig, ModuleSteeringKeyboardLongitudinalSink
from ats_cinepilot.bridge.keyboard_controls import KeyboardControlConfig
from ats_cinepilot.bridge.scs_controls import ModuleControlConfig
from ats_cinepilot.bridge.scs_telemetry import SharedMemoryV2Config, SharedMemoryV2TelemetrySource
from ats_cinepilot.domain.types import VehicleCommand
from ats_cinepilot.ops.config import cfg_get, resolve_config


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", action="append", required=True)
    parser.add_argument("--target-speed-mps", type=float, default=0.15)
    parser.add_argument("--pulse-ms", type=int, default=400)
    parser.add_argument("--max-pulses", type=int, default=8)
    args = parser.parse_args()

    cfg = resolve_config(args.config)
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
    sink = ModuleSteeringKeyboardLongitudinalSink(
        HybridControlConfig(
            module=ModuleControlConfig(
                module_name=cfg_get(cfg, "control.module_name"),
                class_name=cfg_get(cfg, "control.class_name"),
                apply_method=cfg_get(cfg, "control.apply_method", ""),
                neutral_method=cfg_get(cfg, "control.neutral_method", ""),
                field_mapping=dict(cfg_get(cfg, "control.field_mapping", {})),
                module_search_paths=list(cfg_get(cfg, "control.module_search_paths", [])),
            ),
            keyboard=KeyboardControlConfig(
                steer_left_key=str(cfg_get(cfg, "control.keyboard.steer_left_key", "a")),
                steer_right_key=str(cfg_get(cfg, "control.keyboard.steer_right_key", "d")),
                throttle_key=str(cfg_get(cfg, "control.keyboard.throttle_key", "w")),
                brake_key=str(cfg_get(cfg, "control.keyboard.brake_key", "s")),
                steering_threshold=float(cfg_get(cfg, "control.keyboard.steering_threshold", 0.01)),
                throttle_threshold=float(cfg_get(cfg, "control.keyboard.throttle_threshold", 0.08)),
                brake_threshold=float(cfg_get(cfg, "control.keyboard.brake_threshold", 0.08)),
                longitudinal_pwm_period_s=float(
                    cfg_get(cfg, "control.keyboard.longitudinal_pwm_period_s", 0.25)
                ),
            ),
        )
    )
    source.connect()
    sink.connect()
    try:
        speed = _read_speed(source)
        print(f"initial_speed_mps={speed:.3f}")
        pulses = 0
        while speed > args.target_speed_mps and pulses < args.max_pulses:
            pulses += 1
            sink.apply(VehicleCommand(steering=0.0, throttle=0.0, brake=1.0))
            time.sleep(max(0.05, args.pulse_ms / 1000.0))
            sink.neutralize()
            time.sleep(0.2)
            speed = _read_speed(source)
            print(f"pulse={pulses} speed_mps={speed:.3f}")
        print(f"final_speed_mps={speed:.3f}")
        if speed > args.target_speed_mps:
            raise SystemExit(
                f"vehicle did not settle below target speed: {speed:.3f} > {args.target_speed_mps:.3f}"
            )
    finally:
        sink.neutralize()
        source.close()


def _read_speed(source: SharedMemoryV2TelemetrySource) -> float:
    frame = None
    for _ in range(3):
        frame = source.read()
        if frame is None:
            time.sleep(0.05)
            continue
    if frame is None:
        raise SystemExit(f"failed to read live telemetry while stopping: {source.last_error or 'unknown error'}")
    return float(frame.speed_mps)


if __name__ == "__main__":
    main()
