from types import SimpleNamespace

from ats_cinepilot.domain.types import MatchedEdge, Pose2D, PreviewPath, PreviewPoint, RouteHint, TelemetryFrame, VehicleCommand
from ats_cinepilot.safety.demo_cage import DemoCageConfig, DemoCageDecision, DemoSafetyCage, resolve_demo_command


def _frame(speed_mps: float = 3.0) -> TelemetryFrame:
    return TelemetryFrame(
        mono_time_s=0.0,
        game_tick=1,
        paused=False,
        speed_mps=speed_mps,
        speed_limit_mps=20.0,
        nav_distance_m=100.0,
        pose=Pose2D(0.0, 0.0, 0.0),
    )


def _matched(
    edge_id: str = "ab",
    progress_m: float = 10.0,
    *,
    cross_track_error_m: float = 0.05,
    heading_error_rad: float = 0.01,
    confidence: float = 0.99,
    travel_direction: str = "forward",
) -> MatchedEdge:
    return MatchedEdge(
        edge_id=edge_id,
        lane_id=None,
        progress_m=progress_m,
        cross_track_error_m=cross_track_error_m,
        heading_error_rad=heading_error_rad,
        confidence=confidence,
        travel_direction=travel_direction,
    )


def _hint(confidence: float = 0.7) -> RouteHint:
    return RouteHint("map_fallback", 0.0, 1.0, None, confidence)


def _path() -> PreviewPath:
    return PreviewPath(points=[PreviewPoint(0.0, 0.0, 0.0, 4.0)], horizon_m=40.0, branch_id=None, confidence=0.9)


def _telemetry_state(**overrides):
    defaults = {
        "pose_source": "authoritative_absolute",
        "heading_source": "absolute_position_hold",
        "anchor_heading_locked": True,
        "discontinuity_detected": False,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _matcher_diag(**overrides):
    defaults = {
        "candidate_count": 1,
        "nearest_edge_distance_m": 0.05,
        "failure_reason": None,
        "direction_confidence_state": "confident",
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def test_demo_safety_cage_requires_consecutive_qualifying_frames():
    cage = DemoSafetyCage(
        DemoCageConfig(
            enabled=True,
            corridor_name="toy_ab_demo",
            approved_graph_source="toy_graph",
            approved_alignment_mode="anchored_local_toy_graph",
            approved_edge_ids=("ab",),
            min_progress_m=5.0,
            max_progress_m=80.0,
            arm_consecutive_frames=2,
        )
    )

    first = cage.evaluate(
        frame=_frame(),
        matched=_matched(),
        hint=_hint(),
        path=_path(),
        telemetry_state=_telemetry_state(),
        matcher_diagnostics=_matcher_diag(),
        graph_source="toy_graph",
        alignment_mode="anchored_local_toy_graph",
        control_sink_healthy=True,
        manual_override_active=False,
    )
    second = cage.evaluate(
        frame=_frame(),
        matched=_matched(),
        hint=_hint(),
        path=_path(),
        telemetry_state=_telemetry_state(),
        matcher_diagnostics=_matcher_diag(),
        graph_source="toy_graph",
        alignment_mode="anchored_local_toy_graph",
        control_sink_healthy=True,
        manual_override_active=False,
    )

    assert first.allow_control is False
    assert first.reason == "arming"
    assert first.qualifying_frames == 1
    assert second.allow_control is True
    assert second.reason == "armed"
    assert second.qualifying_frames == 2


def test_demo_safety_cage_resets_when_progress_leaves_corridor():
    cage = DemoSafetyCage(
        DemoCageConfig(
            enabled=True,
            corridor_name="toy_ab_demo",
            approved_graph_source="toy_graph",
            approved_alignment_mode="anchored_local_toy_graph",
            approved_edge_ids=("ab",),
            min_progress_m=5.0,
            max_progress_m=80.0,
            arm_consecutive_frames=2,
        )
    )

    cage.evaluate(
        frame=_frame(),
        matched=_matched(progress_m=10.0),
        hint=_hint(),
        path=_path(),
        telemetry_state=_telemetry_state(),
        matcher_diagnostics=_matcher_diag(),
        graph_source="toy_graph",
        alignment_mode="anchored_local_toy_graph",
        control_sink_healthy=True,
        manual_override_active=False,
    )
    outside = cage.evaluate(
        frame=_frame(),
        matched=_matched(progress_m=82.0),
        hint=_hint(),
        path=_path(),
        telemetry_state=_telemetry_state(),
        matcher_diagnostics=_matcher_diag(),
        graph_source="toy_graph",
        alignment_mode="anchored_local_toy_graph",
        control_sink_healthy=True,
        manual_override_active=False,
    )
    rearm = cage.evaluate(
        frame=_frame(),
        matched=_matched(progress_m=12.0),
        hint=_hint(),
        path=_path(),
        telemetry_state=_telemetry_state(),
        matcher_diagnostics=_matcher_diag(),
        graph_source="toy_graph",
        alignment_mode="anchored_local_toy_graph",
        control_sink_healthy=True,
        manual_override_active=False,
    )

    assert outside.allow_control is False
    assert outside.reason == "progress_out_of_bounds"
    assert outside.qualifying_frames == 0
    assert rearm.allow_control is False
    assert rearm.reason == "arming"
    assert rearm.qualifying_frames == 1


def test_demo_safety_cage_allows_bootstrap_when_stationary_heading_is_unknown():
    cage = DemoSafetyCage(
        DemoCageConfig(
            enabled=True,
            corridor_name="toy_ab_demo",
            approved_graph_source="toy_graph",
            approved_alignment_mode="anchored_local_toy_graph",
            approved_edge_ids=("ab",),
            min_progress_m=5.0,
            max_progress_m=80.0,
            bootstrap_max_speed_mps=0.5,
            bootstrap_throttle=0.35,
        )
    )

    bootstrap = cage.evaluate(
        frame=_frame(speed_mps=0.0),
        matched=_matched(progress_m=10.0),
        hint=_hint(),
        path=_path(),
        telemetry_state=_telemetry_state(heading_source="unknown", anchor_heading_locked=False),
        matcher_diagnostics=_matcher_diag(),
        graph_source="toy_graph",
        alignment_mode="anchored_local_toy_graph",
        control_sink_healthy=True,
        manual_override_active=False,
    )

    assert bootstrap.allow_control is True
    assert bootstrap.armed is False
    assert bootstrap.reason == "bootstrap"


def test_demo_safety_cage_bootstrap_does_not_ignore_corridor_mismatch():
    cage = DemoSafetyCage(
        DemoCageConfig(
            enabled=True,
            corridor_name="toy_ab_demo",
            approved_graph_source="toy_graph",
            approved_alignment_mode="anchored_local_toy_graph",
            approved_edge_ids=("ab",),
            min_progress_m=5.0,
            max_progress_m=80.0,
            bootstrap_max_speed_mps=0.5,
            bootstrap_throttle=0.35,
        )
    )

    blocked = cage.evaluate(
        frame=_frame(speed_mps=0.0),
        matched=_matched(edge_id="bc", progress_m=10.0),
        hint=_hint(),
        path=_path(),
        telemetry_state=_telemetry_state(),
        matcher_diagnostics=_matcher_diag(),
        graph_source="toy_graph",
        alignment_mode="anchored_local_toy_graph",
        control_sink_healthy=True,
        manual_override_active=False,
    )

    assert blocked.allow_control is False
    assert blocked.reason == "outside_corridor_edge"


def test_demo_safety_cage_rejects_missing_preview_path():
    cage = DemoSafetyCage(
        DemoCageConfig(
            enabled=True,
            corridor_name="toy_ab_demo",
            approved_graph_source="toy_graph",
            approved_alignment_mode="anchored_local_toy_graph",
            approved_edge_ids=("ab",),
            min_progress_m=5.0,
            max_progress_m=80.0,
        )
    )

    blocked = cage.evaluate(
        frame=_frame(),
        matched=_matched(progress_m=10.0),
        hint=_hint(),
        path=None,
        telemetry_state=_telemetry_state(),
        matcher_diagnostics=_matcher_diag(),
        graph_source="toy_graph",
        alignment_mode="anchored_local_toy_graph",
        control_sink_healthy=True,
        manual_override_active=False,
    )

    assert blocked.allow_control is False
    assert blocked.reason == "preview_path_missing"


def test_demo_safety_cage_requires_dense_corridor_start_edge_before_arming():
    cage = DemoSafetyCage(
        DemoCageConfig(
            enabled=True,
            corridor_name="dense_demo_curve",
            approved_graph_source="curated_dense_local_corridor_graph",
            approved_alignment_mode="ats_absolute_identity",
            approved_edge_ids=("edge_a", "edge_b"),
            approved_edge_sequence=("edge_a", "edge_b"),
            start_edge_id="edge_a",
            start_progress_max_m=8.0,
        )
    )

    blocked = cage.evaluate(
        frame=_frame(speed_mps=0.0),
        matched=_matched(edge_id="edge_b", progress_m=1.0),
        hint=_hint(),
        path=_path(),
        telemetry_state=_telemetry_state(),
        matcher_diagnostics=_matcher_diag(),
        graph_source="curated_dense_local_corridor_graph",
        alignment_mode="ats_absolute_identity",
        control_sink_healthy=True,
        manual_override_active=False,
    )

    assert blocked.allow_control is False
    assert blocked.reason == "corridor_start_edge_required"


def test_demo_safety_cage_rejects_dense_corridor_start_progress_below_window():
    cage = DemoSafetyCage(
        DemoCageConfig(
            enabled=True,
            corridor_name="dense_demo_curve",
            approved_graph_source="curated_dense_local_corridor_graph",
            approved_alignment_mode="ats_absolute_identity",
            approved_edge_ids=("edge_a", "edge_b"),
            approved_edge_sequence=("edge_a", "edge_b"),
            start_edge_id="edge_a",
            start_progress_min_m=12.0,
            start_progress_max_m=28.0,
        )
    )

    blocked = cage.evaluate(
        frame=_frame(speed_mps=0.0),
        matched=_matched(edge_id="edge_a", progress_m=8.0),
        hint=_hint(),
        path=_path(),
        telemetry_state=_telemetry_state(),
        matcher_diagnostics=_matcher_diag(),
        graph_source="curated_dense_local_corridor_graph",
        alignment_mode="ats_absolute_identity",
        control_sink_healthy=True,
        manual_override_active=False,
    )

    assert blocked.allow_control is False
    assert blocked.reason == "corridor_start_progress_low"


def test_demo_safety_cage_primes_start_window_once_even_if_other_guards_fail():
    cage = DemoSafetyCage(
        DemoCageConfig(
            enabled=True,
            corridor_name="dense_demo_curve",
            approved_graph_source="curated_dense_local_corridor_graph",
            approved_alignment_mode="ats_absolute_identity",
            approved_edge_ids=("edge_a", "edge_b"),
            approved_edge_sequence=("edge_a", "edge_b"),
            start_edge_id="edge_a",
            start_progress_min_m=12.0,
            start_progress_max_m=28.0,
            max_cross_track_error_m=0.2,
        )
    )

    first = cage.evaluate(
        frame=_frame(speed_mps=0.0),
        matched=_matched(edge_id="edge_a", progress_m=20.0, cross_track_error_m=0.4),
        hint=_hint(),
        path=_path(),
        telemetry_state=_telemetry_state(),
        matcher_diagnostics=_matcher_diag(),
        graph_source="curated_dense_local_corridor_graph",
        alignment_mode="ats_absolute_identity",
        control_sink_healthy=True,
        manual_override_active=False,
    )
    second = cage.evaluate(
        frame=_frame(speed_mps=0.0),
        matched=_matched(edge_id="edge_a", progress_m=32.0, cross_track_error_m=0.4),
        hint=_hint(),
        path=_path(),
        telemetry_state=_telemetry_state(),
        matcher_diagnostics=_matcher_diag(),
        graph_source="curated_dense_local_corridor_graph",
        alignment_mode="ats_absolute_identity",
        control_sink_healthy=True,
        manual_override_active=False,
    )

    assert first.reason == "cross_track_error_high"
    assert second.reason == "cross_track_error_high"


def test_demo_safety_cage_rejects_dense_corridor_sequence_regression():
    cage = DemoSafetyCage(
        DemoCageConfig(
            enabled=True,
            corridor_name="dense_demo_curve",
            approved_graph_source="curated_dense_local_corridor_graph",
            approved_alignment_mode="ats_absolute_identity",
            approved_edge_ids=("edge_a", "edge_b"),
            approved_edge_sequence=("edge_a", "edge_b"),
            start_edge_id="edge_a",
            start_progress_max_m=8.0,
            arm_consecutive_frames=1,
        )
    )

    armed = cage.evaluate(
        frame=_frame(speed_mps=0.0),
        matched=_matched(edge_id="edge_a", progress_m=2.0),
        hint=_hint(),
        path=_path(),
        telemetry_state=_telemetry_state(),
        matcher_diagnostics=_matcher_diag(),
        graph_source="curated_dense_local_corridor_graph",
        alignment_mode="ats_absolute_identity",
        control_sink_healthy=True,
        manual_override_active=False,
    )
    advanced = cage.evaluate(
        frame=_frame(speed_mps=1.5),
        matched=_matched(edge_id="edge_b", progress_m=5.0),
        hint=_hint(),
        path=_path(),
        telemetry_state=_telemetry_state(),
        matcher_diagnostics=_matcher_diag(),
        graph_source="curated_dense_local_corridor_graph",
        alignment_mode="ats_absolute_identity",
        control_sink_healthy=True,
        manual_override_active=False,
    )
    regressed = cage.evaluate(
        frame=_frame(speed_mps=1.5),
        matched=_matched(edge_id="edge_a", progress_m=6.0),
        hint=_hint(),
        path=_path(),
        telemetry_state=_telemetry_state(),
        matcher_diagnostics=_matcher_diag(),
        graph_source="curated_dense_local_corridor_graph",
        alignment_mode="ats_absolute_identity",
        control_sink_healthy=True,
        manual_override_active=False,
    )

    assert armed.allow_control is True
    assert advanced.allow_control is True
    assert regressed.allow_control is False
    assert regressed.reason == "edge_sequence_regressed"


def test_resolve_demo_command_keeps_bootstrap_throttle_until_heading_locks():
    resolved = resolve_demo_command(
        VehicleCommand(steering=0.3, throttle=0.8, brake=0.0),
        DemoCageDecision(allow_control=True, reason="bootstrap", armed=False, qualifying_frames=0),
        DemoCageConfig(enabled=True, bootstrap_throttle=0.35),
    )

    assert resolved.command.steering == 0.3
    assert resolved.command.throttle == 0.35
    assert resolved.command.brake == 0.0
    assert resolved.apply_when_disengaged is True
    assert resolved.mode == "bootstrap"


def test_demo_safety_cage_bootstrap_can_use_corridor_specific_relaxed_thresholds():
    cage = DemoSafetyCage(
        DemoCageConfig(
            enabled=True,
            corridor_name="dense_curated_freeway_demo",
            approved_graph_source="curated_dense_local_corridor_graph",
            approved_alignment_mode="ats_absolute_identity",
            approved_edge_ids=("dense_seg_01",),
            approved_edge_sequence=("dense_seg_01",),
            start_edge_id="dense_seg_01",
            start_progress_max_m=25.0,
            bootstrap_max_speed_mps=0.6,
            bootstrap_throttle=0.30,
            bootstrap_min_match_confidence=0.60,
            bootstrap_max_cross_track_error_m=1.50,
            bootstrap_max_nearest_edge_distance_m=1.50,
        )
    )

    bootstrap = cage.evaluate(
        frame=_frame(speed_mps=0.0),
        matched=_matched(edge_id="dense_seg_01", progress_m=18.0, confidence=0.67, cross_track_error_m=1.34),
        hint=_hint(confidence=0.47),
        path=_path(),
        telemetry_state=_telemetry_state(heading_source="unknown", anchor_heading_locked=False),
        matcher_diagnostics=_matcher_diag(candidate_count=1, nearest_edge_distance_m=1.34),
        graph_source="curated_dense_local_corridor_graph",
        alignment_mode="ats_absolute_identity",
        control_sink_healthy=True,
        manual_override_active=False,
    )

    assert bootstrap.allow_control is True
    assert bootstrap.reason == "bootstrap"


def test_demo_safety_cage_bootstrap_still_rejects_large_dense_corridor_offset():
    cage = DemoSafetyCage(
        DemoCageConfig(
            enabled=True,
            corridor_name="dense_curated_freeway_demo",
            approved_graph_source="curated_dense_local_corridor_graph",
            approved_alignment_mode="ats_absolute_identity",
            approved_edge_ids=("dense_seg_01",),
            approved_edge_sequence=("dense_seg_01",),
            start_edge_id="dense_seg_01",
            start_progress_max_m=25.0,
            bootstrap_max_speed_mps=0.6,
            bootstrap_throttle=0.30,
            bootstrap_min_match_confidence=0.60,
            bootstrap_max_cross_track_error_m=1.50,
            bootstrap_max_nearest_edge_distance_m=1.50,
        )
    )

    blocked = cage.evaluate(
        frame=_frame(speed_mps=0.0),
        matched=_matched(edge_id="dense_seg_01", progress_m=18.0, confidence=0.67, cross_track_error_m=1.81),
        hint=_hint(confidence=0.47),
        path=_path(),
        telemetry_state=_telemetry_state(heading_source="unknown", anchor_heading_locked=False),
        matcher_diagnostics=_matcher_diag(candidate_count=1, nearest_edge_distance_m=1.81),
        graph_source="curated_dense_local_corridor_graph",
        alignment_mode="ats_absolute_identity",
        control_sink_healthy=True,
        manual_override_active=False,
    )

    assert blocked.allow_control is False
    assert blocked.reason == "heading_source_unapproved"


def test_resolve_demo_command_allows_brake_only_assist_on_speed_cap_guard():
    resolved = resolve_demo_command(
        VehicleCommand(steering=0.2, throttle=0.0, brake=0.7),
        DemoCageDecision(allow_control=False, reason="speed_cap_exceeded", armed=False, qualifying_frames=0),
        DemoCageConfig(enabled=True),
    )

    assert resolved.command.steering == 0.0
    assert resolved.command.throttle == 0.0
    assert resolved.command.brake == 0.7
    assert resolved.apply_when_disengaged is True
    assert resolved.mode == "brake_assist"


def test_demo_safety_cage_rejects_out_of_order_dense_corridor_regression():
    cage = DemoSafetyCage(
        DemoCageConfig(
            enabled=True,
            corridor_name="dense_demo",
            approved_graph_source="curated_dense_local_corridor_graph",
            approved_alignment_mode="ats_absolute_identity",
            approved_edge_ids=("edge_a", "edge_b"),
            approved_edge_sequence=("edge_a", "edge_b"),
            completion_edge_id="edge_b",
            completion_max_progress_m=50.0,
            arm_consecutive_frames=1,
        )
    )

    first = cage.evaluate(
        frame=_frame(),
        matched=_matched(edge_id="edge_a", progress_m=10.0),
        hint=_hint(),
        path=_path(),
        telemetry_state=_telemetry_state(),
        matcher_diagnostics=_matcher_diag(),
        graph_source="curated_dense_local_corridor_graph",
        alignment_mode="ats_absolute_identity",
        control_sink_healthy=True,
        manual_override_active=False,
    )
    second = cage.evaluate(
        frame=_frame(),
        matched=_matched(edge_id="edge_b", progress_m=12.0),
        hint=_hint(),
        path=_path(),
        telemetry_state=_telemetry_state(),
        matcher_diagnostics=_matcher_diag(),
        graph_source="curated_dense_local_corridor_graph",
        alignment_mode="ats_absolute_identity",
        control_sink_healthy=True,
        manual_override_active=False,
    )
    regressed = cage.evaluate(
        frame=_frame(),
        matched=_matched(edge_id="edge_a", progress_m=18.0),
        hint=_hint(),
        path=_path(),
        telemetry_state=_telemetry_state(),
        matcher_diagnostics=_matcher_diag(),
        graph_source="curated_dense_local_corridor_graph",
        alignment_mode="ats_absolute_identity",
        control_sink_healthy=True,
        manual_override_active=False,
    )

    assert first.reason == "armed"
    assert second.reason == "armed"
    assert regressed.allow_control is False
    assert regressed.reason == "edge_sequence_regressed"


def test_demo_safety_cage_marks_dense_corridor_complete_at_terminal_progress():
    cage = DemoSafetyCage(
        DemoCageConfig(
            enabled=True,
            corridor_name="dense_demo",
            approved_graph_source="curated_dense_local_corridor_graph",
            approved_alignment_mode="ats_absolute_identity",
            approved_edge_ids=("edge_a", "edge_b"),
            approved_edge_sequence=("edge_a", "edge_b"),
            completion_edge_id="edge_b",
            completion_max_progress_m=50.0,
            arm_consecutive_frames=1,
        )
    )

    cage.evaluate(
        frame=_frame(),
        matched=_matched(edge_id="edge_a", progress_m=10.0),
        hint=_hint(),
        path=_path(),
        telemetry_state=_telemetry_state(),
        matcher_diagnostics=_matcher_diag(),
        graph_source="curated_dense_local_corridor_graph",
        alignment_mode="ats_absolute_identity",
        control_sink_healthy=True,
        manual_override_active=False,
    )
    complete = cage.evaluate(
        frame=_frame(),
        matched=_matched(edge_id="edge_b", progress_m=55.0),
        hint=_hint(),
        path=_path(),
        telemetry_state=_telemetry_state(),
        matcher_diagnostics=_matcher_diag(),
        graph_source="curated_dense_local_corridor_graph",
        alignment_mode="ats_absolute_identity",
        control_sink_healthy=True,
        manual_override_active=False,
    )

    assert complete.allow_control is False
    assert complete.reason == "corridor_complete"
