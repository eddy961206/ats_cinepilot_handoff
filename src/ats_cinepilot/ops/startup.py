from __future__ import annotations

from ats_cinepilot.ops.config import cfg_get


def build_startup_summary(cfg: dict, mode: str) -> list[str]:
    telemetry_source = cfg_get(cfg, "telemetry.source", "json_http")
    control_sink = cfg_get(cfg, "control.sink", "noop")
    hud_preset_path = cfg_get(cfg, "hud.preset_path", "")
    route_provider = "hud" if hud_preset_path else "none"
    hud_capture = "enabled" if hud_preset_path else "disabled"

    return [
        f"startup mode={mode.lower()} live={'yes' if telemetry_source != 'replay' else 'no'}",
        f"telemetry_source={telemetry_source}",
        f"control_sink={control_sink}",
        f"route_provider={route_provider}",
        f"hud_capture={hud_capture}",
        (
            "safety "
            f"telemetry_timeout_ms={cfg_get(cfg, 'safety.telemetry_timeout_ms', 250)} "
            f"min_map_match_confidence={cfg_get(cfg, 'safety.min_map_match_confidence', 0.6)} "
            f"min_route_confidence={cfg_get(cfg, 'safety.min_route_confidence', 0.55)}"
        ),
    ]


def validate_startup_requirements(cfg: dict, mode: str) -> list[str]:
    issues: list[str] = []
    telemetry_source = cfg_get(cfg, "telemetry.source", "json_http")
    control_sink = cfg_get(cfg, "control.sink", "noop")
    mode_lower = mode.lower()

    if telemetry_source == "shared_memory_v2":
        issues.append(
            "telemetry.source=shared_memory_v2 is selected, but the in-loop reader is still not implemented. "
            "Use scripts/inspect_telemetry.py with the live shared-memory config first."
        )

    if mode_lower == "active" and telemetry_source == "replay":
        issues.append("active mode cannot run on replay telemetry.")

    if mode_lower == "active" and control_sink in {"noop", "recording"}:
        issues.append("active mode requires a real control sink, not noop/recording.")

    return issues
