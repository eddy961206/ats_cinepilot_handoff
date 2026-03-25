from types import SimpleNamespace

from ats_cinepilot.domain.types import MatchedEdge, Pose2D, PreviewPath, PreviewPoint, RouteHint, TelemetryFrame
from ats_cinepilot.safety.demo_cage import DemoCageConfig, DemoSafetyCage


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


def _matched(edge_id: str = "ab", progress_m: float = 10.0) -> MatchedEdge:
    return MatchedEdge(
        edge_id=edge_id,
        lane_id=None,
        progress_m=progress_m,
        cross_track_error_m=0.05,
        heading_error_rad=0.01,
        confidence=0.99,
        travel_direction="forward",
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
