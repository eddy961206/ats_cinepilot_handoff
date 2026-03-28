from __future__ import annotations

from ats_cinepilot.ops.config import cfg_get


def build_startup_summary(cfg: dict, mode: str) -> list[str]:
    telemetry_source = cfg_get(cfg, "telemetry.source", "json_http")
    pose_frame_mode = cfg_get(cfg, "telemetry.pose_frame_mode", "unknown")
    control_sink = cfg_get(cfg, "control.sink", "noop")
    hud_preset_path = cfg_get(cfg, "hud.preset_path", "")
    cv_enabled = bool(cfg_get(cfg, "cv.enabled", False))
    route_provider = "hud" if hud_preset_path else "none"
    hud_capture = "enabled" if hud_preset_path else "disabled"
    graph_source = cfg_get(cfg, "map.source_name", "graph_cache")
    alignment_mode = cfg_get(cfg, "map.alignment_mode", "unknown")
    telemetry_line = f"telemetry_source={telemetry_source}"
    if telemetry_source == "shared_memory_v2":
        telemetry_line += f" mapping={cfg_get(cfg, 'telemetry.shared_memory_name', 'SCSTelemetrySharedv2_ats')}"

    if control_sink == "hybrid":
        control_sink_display = "hybrid(module steering + keyboard throttle/brake)"
    else:
        control_sink_display = control_sink

    lines = [
        f"startup mode={mode.lower()} live={'yes' if telemetry_source != 'replay' else 'no'}",
        telemetry_line,
        f"telemetry_pose_frame={pose_frame_mode}",
        f"control_sink={control_sink_display}",
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
        edge_sequence = " -> ".join(cfg_get(cfg, "demo.approved_edge_sequence", [])) or "<none>"
        keyboard_pwm_s = cfg_get(cfg, "control.keyboard.longitudinal_pwm_period_s", 0.0)
        lines.extend(
            [
                f"demo_enabled=yes corridor={cfg_get(cfg, 'demo.corridor_name', 'unnamed')}",
                f"demo_edge_ids={edge_ids}",
                f"demo_edge_sequence={edge_sequence}",
                f"demo_contract_path={cfg_get(cfg, 'demo.contract_path', '') or '<none>'}",
                f"demo_max_speed_mps={cfg_get(cfg, 'demo.max_speed_mps', 0.0)}",
                f"demo_focus_required={'yes' if control_sink == 'hybrid' else 'no'}",
                f"keyboard_longitudinal_pwm_s={keyboard_pwm_s}",
                f"manual_override_flag={cfg_get(cfg, 'manual_override.flag_path', '') or '<none>'}",
            ]
        )

    if cv_enabled:
        lines.extend(
            [
                (
                    "cv_enabled=yes "
                    f"lane={'yes' if cfg_get(cfg, 'cv.lane.enabled', True) else 'no'} "
                    f"vehicles={'yes' if cfg_get(cfg, 'cv.vehicles.enabled', True) else 'no'} "
                    f"barrier={'yes' if cfg_get(cfg, 'cv.barrier.enabled', False) else 'no'}"
                ),
                (
                    "cv_artifacts "
                    f"show_window={'yes' if cfg_get(cfg, 'cv.show_window', False) else 'no'} "
                    f"save_video={'yes' if cfg_get(cfg, 'cv.save_video', True) else 'no'} "
                    f"save_frames={'yes' if cfg_get(cfg, 'cv.save_frames', False) else 'no'}"
                ),
                (
                    "cv_guard "
                    f"enabled={'yes' if cfg_get(cfg, 'cv.guard.enabled', False) else 'no'} "
                    f"lane_guard={'yes' if cfg_get(cfg, 'cv.guard.enable_lane_guard', False) else 'no'} "
                    f"lead_guard={'yes' if cfg_get(cfg, 'cv.guard.enable_lead_vehicle_guard', True) else 'no'}"
                ),
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
        if control_sink != "hybrid":
            issues.append("demo active mode requires control.sink=hybrid.")
        approved_graph_source = cfg_get(cfg, "demo.approved_graph_source", "")
        approved_alignment_mode = cfg_get(cfg, "demo.approved_alignment_mode", "")
        map_source_name = cfg_get(cfg, "map.source_name", "")
        map_alignment_mode = cfg_get(cfg, "map.alignment_mode", "")
        if not approved_graph_source:
            issues.append("demo.approved_graph_source is required when demo.enabled=true.")
        elif approved_graph_source != map_source_name:
            issues.append("demo.approved_graph_source must match map.source_name in active demo mode.")
        if not approved_alignment_mode:
            issues.append("demo.approved_alignment_mode is required when demo.enabled=true.")
        elif approved_alignment_mode != map_alignment_mode:
            issues.append("demo.approved_alignment_mode must match map.alignment_mode in active demo mode.")
        pose_frame_mode = cfg_get(cfg, "telemetry.pose_frame_mode", "")
        if map_alignment_mode == "ats_absolute_identity" and pose_frame_mode != "world_absolute":
            issues.append(
                "demo active mode with map.alignment_mode=ats_absolute_identity "
                "requires telemetry.pose_frame_mode=world_absolute."
            )
        if not cfg_get(cfg, "demo.approved_edge_ids", []):
            issues.append("demo.approved_edge_ids must not be empty when demo.enabled=true.")
        contract_path = cfg_get(cfg, "demo.contract_path", "")
        if contract_path and not __import__("pathlib").Path(contract_path).exists():
            issues.append("demo.contract_path must exist when set in active demo mode.")
        if cfg_get(cfg, "demo.approved_edge_sequence", []) and not contract_path:
            issues.append("demo.contract_path is required when demo.approved_edge_sequence is set.")
        if cfg_get(cfg, "demo.approved_edge_sequence", []) and not cfg_get(cfg, "demo.completion_edge_id", ""):
            issues.append("demo.completion_edge_id is required when demo.approved_edge_sequence is set.")

    if bool(cfg_get(cfg, "cv.enabled", False)):
        if mode_lower == "active" and control_sink == "hybrid" and bool(cfg_get(cfg, "cv.show_window", False)):
            issues.append("cv.show_window must be false in active mode to avoid stealing ATS focus.")

    return issues
