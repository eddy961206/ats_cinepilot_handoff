from ats_cinepilot.domain.enums import DisengageReason
from ats_cinepilot.domain.types import MatchedEdge, Pose2D, PreviewPath, PreviewPoint, RouteHint, TelemetryFrame, VehicleCommand
from ats_cinepilot.safety.arbiter import RuleBasedSafetyPolicy, SafetyConfig


def test_safety_disengages_when_route_confidence_low():
    policy = RuleBasedSafetyPolicy(SafetyConfig(min_route_confidence=0.8))
    frame = TelemetryFrame(
        mono_time_s=0.0,
        game_tick=1,
        paused=False,
        speed_mps=10.0,
        speed_limit_mps=20.0,
        nav_distance_m=100.0,
        pose=Pose2D(0, 0, 0),
    )
    matched = MatchedEdge("e1", None, 0.0, 0.2, 0.0, 0.9)
    hint = RouteHint("hud", 0.0, 0.0, None, 0.2)
    path = PreviewPath([PreviewPoint(0, 0, 0.0, 20.0)], 10.0, None, 0.9)
    cmd = VehicleCommand(0.0, 0.0, 0.0)
    decision = policy.evaluate(frame, matched, hint, path, cmd)
    assert decision.allow_control is False
    assert decision.reason == DisengageReason.ROUTE_CONFIDENCE_LOW
