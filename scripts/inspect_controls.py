from __future__ import annotations

import argparse
import importlib
from pathlib import Path

from ats_cinepilot.bridge.live_diagnostics import (
    ControlProbeStatus,
    classify_control_probe_status,
    find_ats_game_dir,
    process_is_running,
)
from ats_cinepilot.bridge.scs_controls import DynamicModuleControlSink, ModuleControlConfig, NoopControlSink
from ats_cinepilot.bridge.windows_probes import probe_named_mapping
from ats_cinepilot.domain.types import VehicleCommand
from ats_cinepilot.ops.config import cfg_get, resolve_config


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", action="append", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    cfg = resolve_config(args.config)
    sink_name = cfg_get(cfg, "control.sink", "noop")
    ats_running = process_is_running(["amtrucks.exe", "amtrucks"])
    print(f"control sink: {sink_name}")
    print(f"ats running: {'yes' if ats_running else 'no'}")
    if sink_name == "module":
        _inspect_module_target(cfg, ats_running)

    if sink_name == "noop":
        sink = NoopControlSink()
    else:
        sink = DynamicModuleControlSink(
            ModuleControlConfig(
                module_name=cfg_get(cfg, "control.module_name"),
                class_name=cfg_get(cfg, "control.class_name"),
                apply_method=cfg_get(cfg, "control.apply_method", ""),
                neutral_method=cfg_get(cfg, "control.neutral_method", ""),
                field_mapping=dict(cfg_get(cfg, "control.field_mapping", {})),
            )
        )

    if args.dry_run:
        print("dry-run requested; skipping apply/neutralize")
        return

    sink.connect()
    sink.apply(VehicleCommand(steering=0.1, throttle=0.0, brake=0.0))
    sink.neutralize()
    print("control sink smoke test completed")


def _inspect_module_target(cfg: dict, ats_running: bool) -> None:
    module_name = cfg_get(cfg, "control.module_name")
    class_name = cfg_get(cfg, "control.class_name")
    field_mapping = dict(cfg_get(cfg, "control.field_mapping", {}))
    plugin_dll_name = cfg_get(cfg, "control.plugin_dll_name", "scs_sdk_controller.dll")
    game_dir = find_ats_game_dir()
    plugin_path = None
    plugin_present = False
    if game_dir is not None:
        plugin_path = game_dir / "bin" / "win_x64" / "plugins" / plugin_dll_name
        plugin_present = plugin_path.exists()

    print(f"module target: {module_name}.{class_name}")
    try:
        module = importlib.import_module(module_name)
        klass = getattr(module, class_name)
        python_module_present = True
    except Exception as exc:
        print(f"module import: FAILED ({exc})")
        python_module_present = False
        klass = None
        memory_name = cfg_get(cfg, "control.shared_memory_name", r"Local\SCSControls")
        probe = probe_named_mapping(memory_name)
        _print_control_category(
            ats_running=ats_running,
            plugin_present=plugin_present,
            python_module_present=python_module_present,
            field_mapping_ok=False,
            mapping_name=memory_name,
            mapping_present=probe.exists,
            mapping_error=probe.error,
            plugin_path=plugin_path,
        )
        return

    print("module import: OK")
    annotations = dict(getattr(klass, "__annotations__", {}))
    memory_name = getattr(klass, "MEM_NAME", None)
    if memory_name:
        probe = probe_named_mapping(memory_name)
        status = "VISIBLE" if probe.exists else "not visible"
        suffix = "" if probe.error is None else f" ({probe.error})"
        print(f"named mapping probe before attach: {memory_name} -> {status}{suffix}")
        if not probe.exists:
            print("note: some clients can create the mapping themselves, so attach success alone does not prove ATS/plugin is listening")
    else:
        probe = probe_named_mapping(cfg_get(cfg, "control.shared_memory_name", r"Local\SCSControls"))
        memory_name = cfg_get(cfg, "control.shared_memory_name", r"Local\SCSControls")

    missing_fields: list[str] = []
    for logical_name, fallback in (
        ("steering", "steering"),
        ("throttle", "throttle"),
        ("brake", "brake"),
        ("left_blinker", "left_blinker"),
        ("right_blinker", "right_blinker"),
    ):
        actual_name = field_mapping.get(logical_name, fallback)
        if actual_name not in annotations and not hasattr(klass, actual_name):
            missing_fields.append(f"{logical_name} -> {actual_name}")

    if missing_fields:
        print("field mapping check: FAILED")
        for item in missing_fields:
            print(f"  - missing: {item}")
        field_mapping_ok = False
    else:
        print("field mapping check: OK")
        field_mapping_ok = True

    print(f"expected control plugin DLL: {plugin_path if plugin_path else plugin_dll_name}")
    print(f"plugin DLL present: {'yes' if plugin_present else 'no'}")
    _print_control_category(
        ats_running=ats_running,
        plugin_present=plugin_present,
        python_module_present=python_module_present,
        field_mapping_ok=field_mapping_ok,
        mapping_name=memory_name,
        mapping_present=probe.exists,
        mapping_error=probe.error,
        plugin_path=plugin_path,
    )


def _print_control_category(
    *,
    ats_running: bool,
    plugin_present: bool,
    python_module_present: bool,
    field_mapping_ok: bool,
    mapping_name: str,
    mapping_present: bool,
    mapping_error: str | None,
    plugin_path: Path | None,
) -> None:
    category, details = classify_control_probe_status(
        ControlProbeStatus(
            ats_running=ats_running,
            plugin_dll_present=plugin_present,
            python_module_present=python_module_present,
            field_mapping_ok=field_mapping_ok,
            mapping_name=mapping_name,
            mapping_present=mapping_present,
            mapping_error=mapping_error,
        )
    )
    print(f"control status: {category}")
    if plugin_path and not plugin_present:
        print(f"  - expected plugin DLL missing: {plugin_path}")
    for detail in details:
        print(f"  - {detail}")


if __name__ == "__main__":
    main()
