from ats_cinepilot.domain.types import Pose2D, PreviewPath, PreviewPoint, TelemetryFrame
from ats_cinepilot.planner.speed_profile import SpeedPlanner, SpeedPlannerConfig


def test_speed_planner_reduces_speed_on_curve():
    planner = SpeedPlanner(SpeedPlannerConfig(max_lateral_accel_mps2=1.8, user_speed_cap_mps=25.0))
    path = PreviewPath(
        points=[
            PreviewPoint(0, 0, 0.0, 25.0),
            PreviewPoint(1, 0, 0.2, 25.0),
            PreviewPoint(2, 1, 0.35, 25.0),
        ],
        horizon_m=30.0,
        branch_id=None,
        confidence=1.0,
    )
    frame = TelemetryFrame(
        mono_time_s=0.0,
        game_tick=1,
        paused=False,
        speed_mps=20.0,
        speed_limit_mps=25.0,
        nav_distance_m=1000.0,
        pose=Pose2D(0, 0, 0),
    )
    target = planner.compute(frame, path)
    assert target.target_mps < 25.0
