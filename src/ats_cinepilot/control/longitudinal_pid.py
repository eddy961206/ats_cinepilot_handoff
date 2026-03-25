from __future__ import annotations

from dataclasses import dataclass

from ats_cinepilot.domain.types import SpeedTarget, TelemetryFrame


@dataclass
class PidConfig:
    kp: float = 0.45
    ki: float = 0.04
    kd: float = 0.08
    brake_bias: float = 0.12
    deadband_mps: float = 0.35
    integral_limit: float = 20.0


class PidSpeedController:
    def __init__(self, config: PidConfig) -> None:
        self.config = config
        self._integral = 0.0
        self._prev_error = 0.0
        self._prev_time = None

    def command(self, frame: TelemetryFrame, target: SpeedTarget) -> tuple[float, float]:
        error = target.target_mps - frame.speed_mps

        if abs(error) < self.config.deadband_mps:
            self._integral = 0.0
            return 0.0, 0.0

        derivative = error - self._prev_error
        if self._prev_error != 0.0 and (error > 0.0) != (self._prev_error > 0.0):
            self._integral = 0.0
        self._integral += error
        self._integral = max(-self.config.integral_limit, min(self.config.integral_limit, self._integral))

        u = (
            self.config.kp * error
            + self.config.ki * self._integral
            + self.config.kd * derivative
        )
        self._prev_error = error

        if u >= 0.0:
            throttle = min(1.0, u)
            brake = 0.0
        else:
            throttle = 0.0
            brake = min(1.0, -u + self.config.brake_bias)
        return throttle, brake
