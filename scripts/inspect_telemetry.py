from __future__ import annotations

import argparse
import json
import pprint
import time
from pathlib import Path

import requests

from ats_cinepilot.bridge.shared_memory_v2_analysis import rank_axis_candidates
from ats_cinepilot.bridge.scs_telemetry import _lookup_dotted
from ats_cinepilot.bridge.scs_telemetry import (
    HttpJsonTelemetrySource,
    JsonTelemetryConfig,
    ReplayTelemetrySource,
    SharedMemoryV2AttachError,
    SharedMemoryV2Config,
    SharedMemoryV2TelemetrySource,
)
from ats_cinepilot.bridge.live_diagnostics import (
    TelemetryProbeStatus,
    classify_telemetry_probe_status,
    find_ats_game_dir,
    process_is_running,
    read_recent_game_log_lines,
)
from ats_cinepilot.bridge.windows_probes import probe_named_mapping
from ats_cinepilot.ops.config import cfg_get, resolve_config


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", action="append", required=True)
    parser.add_argument("--frames", type=int, default=10)
    parser.add_argument("--scan-pose-candidates", action="store_true")
    parser.add_argument("--save-json", default="")
    args = parser.parse_args()

    cfg = resolve_config(args.config)
    source_name = cfg_get(cfg, "telemetry.source", "json_http")
    print(f"telemetry source: {source_name}")
    ats_running = process_is_running(["amtrucks.exe", "amtrucks"])
    print(f"ats running: {'yes' if ats_running else 'no'}")

    if source_name == "replay":
        replay_path = cfg_get(cfg, "logging.replay_path")
        print(f"replay path: {replay_path}")
        source = ReplayTelemetrySource(cfg_get(cfg, "logging.replay_path"))
    elif source_name == "shared_memory_v2":
        _print_shared_memory_diagnostics(
            cfg,
            ats_running,
            frames=max(args.frames, 2),
            scan_pose_candidates=args.scan_pose_candidates,
            save_json=args.save_json,
        )
        return
    else:
        _print_shared_memory_probe(cfg)
        _print_http_probe(cfg)
        source = HttpJsonTelemetrySource(
            JsonTelemetryConfig(
                endpoint=cfg_get(cfg, "telemetry.endpoint"),
                timeout_s=float(cfg_get(cfg, "telemetry.timeout_s", 0.2)),
                field_map=dict(cfg_get(cfg, "telemetry.field_map", {})),
            )
        )
    source.connect()

    for index in range(args.frames):
        frame = source.read()
        if frame is None:
            print(f"frame[{index}]: no frame received")
            continue
        pprint.pprint(frame)


def _print_shared_memory_probe(cfg: dict) -> None:
    configured_names = cfg_get(cfg, "telemetry.shared_memory_names", [])
    probe_names = [*configured_names] if configured_names else [r"Local\SCSTelemetry"]
    print("shared memory probe:")
    for name in probe_names:
        result = probe_named_mapping(name)
        status = "VISIBLE" if result.exists else "not visible"
        suffix = "" if result.error is None else f" ({result.error})"
        print(f"  - {name}: {status}{suffix}")


def _print_http_probe(cfg: dict) -> None:
    endpoint = cfg_get(cfg, "telemetry.endpoint")
    timeout_s = float(cfg_get(cfg, "telemetry.timeout_s", 0.2))
    field_map = dict(cfg_get(cfg, "telemetry.field_map", {}))
    started = time.perf_counter()
    try:
        response = requests.get(endpoint, timeout=timeout_s)
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        response.raise_for_status()
        payload = response.json()
        print(f"http probe: OK {response.status_code} in {elapsed_ms:.1f}ms")
        print("mapped fields:")
        for key, dotted in field_map.items():
            value = _lookup_dotted(payload, dotted, default="<missing>")
            print(f"  - {key} <- {dotted}: {value}")
    except Exception as exc:
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        print(f"http probe: FAILED after {elapsed_ms:.1f}ms ({exc})")


def _print_shared_memory_diagnostics(
    cfg: dict,
    ats_running: bool,
    frames: int,
    scan_pose_candidates: bool,
    save_json: str,
) -> None:
    mapping_name = cfg_get(cfg, "telemetry.shared_memory_name", "SCSTelemetrySharedv2_ats")
    plugin_dll_name = cfg_get(cfg, "telemetry.plugin_dll_name", "atssharedplugin64v2.dll")
    game_dir = find_ats_game_dir()
    plugin_path = None
    plugin_present = False
    if game_dir is not None:
        plugin_path = game_dir / "bin" / "win_x64" / "plugins" / plugin_dll_name
        plugin_present = plugin_path.exists()
    probe = probe_named_mapping(mapping_name)
    recent_log = read_recent_game_log_lines()
    game_log_plugin_loaded = any(plugin_dll_name in line for line in recent_log)
    game_log_initialized = any("Memory telemetry example initialized" in line for line in recent_log)

    print(f"selected shared memory: {mapping_name}")
    print(f"expected plugin DLL: {plugin_path if plugin_path else plugin_dll_name}")
    print(f"mapping visible: {'yes' if probe.exists else 'no'}")
    if probe.error:
        print(f"mapping error: {probe.error}")

    decode_supported: bool | None = None
    decode_error: str | None = None
    tick_advanced: bool | None = None
    if probe.exists:
        decode_supported, decode_error, tick_advanced = _sample_shared_memory_v2(
            mapping_name,
            frames,
            scan_pose_candidates=scan_pose_candidates,
            cfg=cfg,
            save_json=save_json,
        )

    category, details = classify_telemetry_probe_status(
        TelemetryProbeStatus(
            ats_running=ats_running,
            plugin_dll_present=plugin_present,
            plugin_dll_path=str(plugin_path) if plugin_path else None,
            mapping_name=mapping_name,
            mapping_present=probe.exists,
            mapping_error=probe.error,
            game_log_plugin_loaded=game_log_plugin_loaded,
            game_log_initialized=game_log_initialized,
            decode_supported=decode_supported,
            decode_error=decode_error,
            tick_advanced=tick_advanced,
        )
    )
    print(f"telemetry status: {category}")
    for detail in details:
        print(f"  - {detail}")


def _sample_shared_memory_v2(
    mapping_name: str,
    frames: int,
    *,
    scan_pose_candidates: bool,
    cfg: dict,
    save_json: str,
) -> tuple[bool, str | None, bool | None]:
    source = SharedMemoryV2TelemetrySource(
        SharedMemoryV2Config(
            mapping_name=mapping_name,
            absolute_x_offset=cfg_get(cfg, "telemetry.absolute_x_offset"),
            absolute_y_offset=cfg_get(cfg, "telemetry.absolute_y_offset"),
            absolute_z_offset=cfg_get(cfg, "telemetry.absolute_z_offset"),
            absolute_value_format=cfg_get(cfg, "telemetry.absolute_value_format", "f64"),
            pose_frame_mode=cfg_get(cfg, "telemetry.pose_frame_mode", "anchored_local"),
            absolute_heading_min_distance_m=float(cfg_get(cfg, "telemetry.absolute_heading_min_distance_m", 0.25)),
            absolute_discontinuity_distance_m=float(cfg_get(cfg, "telemetry.absolute_discontinuity_distance_m", 25.0)),
        )
    )
    try:
        source.connect()
    except SharedMemoryV2AttachError as exc:
        print(f"decode probe: FAILED ({exc})")
        return False, str(exc), None

    sampled_frames = []
    try:
        for index in range(frames):
            raw = source.read_raw()
            frame = source.decoder.decode(raw)
            state = source.last_state
            if frame is None or state is None:
                print(f"decoded frame[{index}]: FAILED ({source.last_error or 'unknown read error'})")
                return False, source.last_error or "shared_memory_v2 read failed", None
            sampled_frames.append((frame, state, raw))
            print(
                "decoded frame[{index}]: "
                "update_token={tick} paused={paused} speed_mps={speed:.3f} "
                "rpm={rpm:.1f} gear={gear}/{displayed_gear} throttle={throttle:.3f} "
                "pose=({x:.2f}, {z:.2f}, yaw={yaw:.3f})".format(
                    index=index,
                    tick=frame.game_tick,
                    paused=frame.paused,
                    speed=frame.speed_mps,
                    rpm=state.engine_rpm,
                    gear=state.gear,
                    displayed_gear=state.displayed_gear,
                    throttle=state.throttle,
                    x=frame.pose.world_x,
                    z=frame.pose.world_z,
                    yaw=frame.pose.yaw_rad,
                )
            )
            print(
                "  decoded candidates: "
                f"game_tag={state.game_tag!r} state_code={state.state_code:.1f} "
                f"tick_candidate={state.tick_candidate:.6f} "
                f"velocity=({state.velocity_x_mps:.3f}, {state.velocity_z_mps:.3f}) "
                f"pose_source={state.pose_source} pose_frame={state.pose_frame} heading_source={state.heading_source} "
                f"absolute_heading={_fmt_optional(state.absolute_heading_rad)} "
                f"anchor_heading={_fmt_optional(state.anchor_heading_rad)} "
                f"anchor_locked={'yes' if state.anchor_heading_locked else 'no'} "
                f"discontinuity={'yes' if state.discontinuity_detected else 'no'} "
                f"reset_reason={state.anchor_reset_reason or 'n/a'} "
                f"jump_distance={_fmt_optional(state.discontinuity_distance_m)} "
                f"absolute_world=({_fmt_optional(state.absolute_world_x_m)}, {_fmt_optional(state.absolute_world_y_m)}, {_fmt_optional(state.absolute_world_z_m)}) "
                f"speed_limit_kph={_fmt_optional(state.speed_limit_kph_candidate)} "
                f"route_distance_km={_fmt_optional(state.route_distance_km_candidate)} "
                f"route_time_min={_fmt_optional(state.route_time_min_candidate)}"
            )
            if index + 1 < frames:
                time.sleep(0.15)
    finally:
        source.close()

    ticks = [frame.game_tick for frame, _, _ in sampled_frames]
    tick_advanced = len(set(ticks)) > 1
    if scan_pose_candidates:
        rows = [
            {
                "mono_time_s": frame.mono_time_s,
                "raw": raw,
                "velocity_x_mps": state.velocity_x_mps,
                "velocity_z_mps": state.velocity_z_mps,
            }
            for frame, state, raw in sampled_frames
        ]
        print("pose candidate scan:")
        for candidate in rank_axis_candidates(rows, axis="x", top_n=5):
            print(
                f"  - x offset={candidate.offset} format={candidate.value_format} "
                f"corr={candidate.correlation:.4f} slope={candidate.slope:.4f} span={candidate.span:.4f}"
            )
        for candidate in rank_axis_candidates(rows, axis="z", top_n=5):
            print(
                f"  - z offset={candidate.offset} format={candidate.value_format} "
                f"corr={candidate.correlation:.4f} slope={candidate.slope:.4f} span={candidate.span:.4f}"
            )
    if save_json:
        payload = [
            {
                "frame": frame.to_dict(),
                "state": {
                    "game_tag": state.game_tag,
                    "state_code": state.state_code,
                    "tick_candidate": state.tick_candidate,
                    "update_token": state.update_token,
                    "velocity_x_mps": state.velocity_x_mps,
                    "velocity_z_mps": state.velocity_z_mps,
                    "speed_mps": state.speed_mps,
                    "engine_rpm": state.engine_rpm,
                    "gear": state.gear,
                    "displayed_gear": state.displayed_gear,
                    "throttle": state.throttle,
                    "pose_source": state.pose_source,
                    "pose_frame": state.pose_frame,
                    "heading_source": state.heading_source,
                    "absolute_heading_rad": state.absolute_heading_rad,
                    "anchor_heading_rad": state.anchor_heading_rad,
                    "anchor_heading_locked": state.anchor_heading_locked,
                    "discontinuity_detected": state.discontinuity_detected,
                    "discontinuity_distance_m": state.discontinuity_distance_m,
                    "anchor_reset_count": state.anchor_reset_count,
                    "anchor_reset_reason": state.anchor_reset_reason,
                    "absolute_world_x_m": state.absolute_world_x_m,
                    "absolute_world_y_m": state.absolute_world_y_m,
                    "absolute_world_z_m": state.absolute_world_z_m,
                },
            }
            for frame, state, _ in sampled_frames
        ]
        path = Path(save_json)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"saved decode json: {path}")
    print(f"decode probe: OK ({len(sampled_frames)} frames, update_token_changed={'yes' if tick_advanced else 'no'})")
    return True, None, tick_advanced


def _fmt_optional(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.3f}"


if __name__ == "__main__":
    main()
