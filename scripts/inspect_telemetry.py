from __future__ import annotations

import argparse
import pprint
import time

import requests

from ats_cinepilot.bridge.scs_telemetry import _lookup_dotted
from ats_cinepilot.bridge.scs_telemetry import HttpJsonTelemetrySource, JsonTelemetryConfig, ReplayTelemetrySource
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
        _print_shared_memory_diagnostics(cfg, ats_running)
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


def _print_shared_memory_diagnostics(cfg: dict, ats_running: bool) -> None:
    mapping_name = cfg_get(cfg, "telemetry.shared_memory_name", "SCSTelemetrySharedv2")
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
        )
    )
    print(f"telemetry status: {category}")
    for detail in details:
        print(f"  - {detail}")


if __name__ == "__main__":
    main()
