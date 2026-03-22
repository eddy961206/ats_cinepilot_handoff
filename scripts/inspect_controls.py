from __future__ import annotations

import argparse
import importlib

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
    print(f"control sink: {sink_name}")
    if sink_name == "module":
        _inspect_module_target(cfg)

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


def _inspect_module_target(cfg: dict) -> None:
    module_name = cfg_get(cfg, "control.module_name")
    class_name = cfg_get(cfg, "control.class_name")
    field_mapping = dict(cfg_get(cfg, "control.field_mapping", {}))
    print(f"module target: {module_name}.{class_name}")
    try:
        module = importlib.import_module(module_name)
        klass = getattr(module, class_name)
    except Exception as exc:
        print(f"module import: FAILED ({exc})")
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
    else:
        print("field mapping check: OK")


if __name__ == "__main__":
    main()
