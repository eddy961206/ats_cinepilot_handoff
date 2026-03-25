from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_yaml(path: str | Path) -> dict[str, Any]:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}


def deep_merge(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    out = dict(left)
    for key, value in right.items():
        if key in out and isinstance(out[key], dict) and isinstance(value, dict):
            out[key] = deep_merge(out[key], value)
        else:
            out[key] = value
    return out


def resolve_config(paths: list[str | Path]) -> dict[str, Any]:
    cfg: dict[str, Any] = {}
    for path in paths:
        cfg = deep_merge(cfg, _resolve_config_path(Path(path), seen=set()))
    return cfg


def cfg_get(cfg: dict[str, Any], dotted: str, default: Any = None) -> Any:
    node: Any = cfg
    for part in dotted.split("."):
        if isinstance(node, dict) and part in node:
            node = node[part]
        else:
            return default
    return node


def _resolve_config_path(path: Path, seen: set[Path]) -> dict[str, Any]:
    resolved = path.resolve()
    if resolved in seen:
        chain = " -> ".join(str(p) for p in [*seen, resolved])
        raise ValueError(f"config extends cycle detected: {chain}")

    payload = load_yaml(resolved)
    extends = payload.pop("extends", [])
    if isinstance(extends, (str, Path)):
        extends = [extends]

    merged: dict[str, Any] = {}
    child_seen = set(seen)
    child_seen.add(resolved)
    for extended in extends:
        extended_path = Path(extended)
        if not extended_path.is_absolute():
            extended_path = resolved.parent / extended_path
        merged = deep_merge(merged, _resolve_config_path(extended_path, seen=child_seen))

    return deep_merge(merged, payload)


def validate_runtime_config(cfg: dict[str, Any], mode: str = "shadow") -> list[str]:
    issues: list[str] = []

    map_cache_path = cfg_get(cfg, "map.cache_path")
    if not map_cache_path:
        issues.append("map.cache_path is required")
    elif not Path(map_cache_path).exists():
        issues.append(f"map.cache_path does not exist: {map_cache_path}")

    telemetry_source = cfg_get(cfg, "telemetry.source", "json_http")
    if telemetry_source == "replay":
        replay_path = cfg_get(cfg, "logging.replay_path")
        if not replay_path:
            issues.append("logging.replay_path is required when telemetry.source=replay")
        elif not Path(replay_path).exists():
            issues.append(f"logging.replay_path does not exist: {replay_path}")
    elif telemetry_source == "shared_memory_v2":
        shared_memory_name = cfg_get(cfg, "telemetry.shared_memory_name", "SCSTelemetrySharedv2_ats")
        if not shared_memory_name:
            issues.append("telemetry.shared_memory_name is required when telemetry.source=shared_memory_v2")
    elif telemetry_source == "json_http":
        endpoint = cfg_get(cfg, "telemetry.endpoint")
        if not endpoint:
            issues.append("telemetry.endpoint is required when telemetry.source=json_http")
        field_map = dict(cfg_get(cfg, "telemetry.field_map", {}))
        for required_key in (
            "paused",
            "speed_mps",
            "pose.world_x",
            "pose.world_z",
            "pose.yaw_rad",
        ):
            if not field_map.get(required_key):
                issues.append(f"telemetry.field_map.{required_key} is required for json_http")
    else:
        issues.append(f"telemetry.source is not supported: {telemetry_source}")

    hud_preset_path = cfg_get(cfg, "hud.preset_path")
    if hud_preset_path and not Path(hud_preset_path).exists():
        issues.append(f"hud.preset_path does not exist: {hud_preset_path}")

    control_sink = cfg_get(cfg, "control.sink", "noop")
    if control_sink == "module" and mode.lower() == "active":
        if not cfg_get(cfg, "control.module_name"):
            issues.append("control.module_name is required when control.sink=module in active mode")
        if not cfg_get(cfg, "control.class_name"):
            issues.append("control.class_name is required when control.sink=module in active mode")
        for search_path in cfg_get(cfg, "control.module_search_paths", []):
            if not Path(search_path).exists():
                issues.append(f"control.module_search_paths entry does not exist: {search_path}")

    return issues
