from __future__ import annotations

from ats_cinepilot.ops.config import cfg_get


def build_startup_summary(cfg: dict, mode: str) -> list[str]:
    telemetry_source = cfg_get(cfg, "telemetry.source", "json_http")
    control_sink = cfg_get(cfg, "control.sink", "noop")
    hud_preset_path = cfg_get(cfg, "hud.preset_path", "")
    route_provider = "hud" if hud_preset_path else "none"
    hud_capture = "enabled" if hud_preset_path else "disabled"
    graph_source = cfg_get(cfg, "map.source_name", "graph_cache")
    alignment_mode = cfg_get(cfg, "map.alignment_mode", "unknown")
    telemetry_line = f"telemetry_source={telemetry_source}"
    if telemetry_source == "shared_memory_v2":
        telemetry_line += f" mapping={cfg_get(cfg, 'telemetry.shared_memory_name', 'SCSTelemetrySharedv2_ats')}"

    lines = [
        f"startup mode={mode.lower()} live={'yes' if telemetry_source != 'replay' else 'no'}",
        telemetry_line,
        f"control_sink={control_sink}",
        f"route_provider={route_provider}",
        f"hud_capture={hud_capture}",
        f"graph_source={graph_source}",
        f"alignment_mode={alignment_mode}",
        (
            "safety "
            f"telemetry_timeout_ms={cfg_get(cfg, 'safety.telemetry_timeout_ms', 250)} "
            f"min_map_match_confidence={cfg_get(cfg, 'safety.min_map_match_confidence', 0.6)} "
            f"min_route_confidence={cfg_get(cfg, 'safety.min_route_confidence', 0.55)}"
        ),
    ]

    if cfg_get(cfg, "demo.enabled", False):
        edge_ids = ",".join(cfg_get(cfg, "demo.approved_edge_ids", [])) or "<none>"
        lines.extend(
            [
                f"demo_enabled=yes corridor={cfg_get(cfg, 'demo.corridor_name', 'unnamed')}",
                f"demo_edge_ids={edge_ids}",
                f"demo_max_speed_mps={cfg_get(cfg, 'demo.max_speed_mps', 0.0)}",
                f"manual_override_flag={cfg_get(cfg, 'manual_override.flag_path', '') or '<none>'}",
            ]
        )

    return lines


def validate_startup_requirements(cfg: dict, mode: str) -> list[str]:
    issues: list[str] = []
    telemetry_source = cfg_get(cfg, "telemetry.source", "json_http")
    control_sink = cfg_get(cfg, "control.sink", "noop")
    mode_lower = mode.lower()

    if mode_lower == "active" and telemetry_source == "replay":
        issues.append("active mode cannot run on replay telemetry.")

    if mode_lower == "active" and control_sink in {"noop", "recording"}:
        issues.append("active mode requires a real control sink, not noop/recording.")

    if mode_lower == "active" and cfg_get(cfg, "demo.enabled", False):
        if telemetry_source != "shared_memory_v2":
            issues.append("demo active mode requires telemetry.source=shared_memory_v2.")
        if control_sink != "module":
            issues.append("demo active mode requires control.sink=module.")
        if not cfg_get(cfg, "demo.approved_graph_source", ""):
            issues.append("demo.approved_graph_source is required when demo.enabled=true.")
        if not cfg_get(cfg, "demo.approved_alignment_mode", ""):
            issues.append("demo.approved_alignment_mode is required when demo.enabled=true.")
        if not cfg_get(cfg, "demo.approved_edge_ids", []):
            issues.append("demo.approved_edge_ids must not be empty when demo.enabled=true.")

    return issues
