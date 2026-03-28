from ats_cinepilot.control.longitudinal_pid import PidConfig, PidSpeedController
from ats_cinepilot.domain.types import Pose2D, SpeedTarget, TelemetryFrame


def _frame(speed_mps: float) -> TelemetryFrame:
    return TelemetryFrame(
        mono_time_s=0.0,
        game_tick=1,
        paused=False,
        speed_mps=speed_mps,
        speed_limit_mps=20.0,
        nav_distance_m=None,
        pose=Pose2D(0.0, 0.0, 0.0),
    )


def _target(target_mps: float) -> SpeedTarget:
    return SpeedTarget(target_mps=target_mps, hard_cap_mps=target_mps, reason="test")


def test_pid_speed_controller_brakes_after_integral_windup_when_overspeed():
    controller = PidSpeedController(
        PidConfig(
            kp=0.18,
            ki=0.02,
            kd=0.04,
            brake_bias=0.05,
            deadband_mps=0.15,
        )
    )

    for _ in range(30):
        throttle, brake = controller.command(_frame(speed_mps=0.0), _target(target_mps=4.0))
        assert throttle > 0.0
        assert brake == 0.0

    throttle, brake = controller.command(_frame(speed_mps=5.0), _target(target_mps=4.0))

    assert throttle == 0.0
    assert brake > 0.0


def test_pid_speed_controller_commands_throttle_when_below_target():
    controller = PidSpeedController(PidConfig())

    throttle, brake = controller.command(_frame(speed_mps=1.5), _target(target_mps=4.0))

    assert throttle > 0.0
    assert brake == 0.0
