from __future__ import annotations

import math
from dataclasses import dataclass

from ats_cinepilot.domain.types import PreviewPath, TelemetryFrame


@dataclass
class AdaptivePurePursuitConfig:
    wheelbase_m: float = 6.0
    steering_gain: float = 1.2
    max_steering_cmd: float = 1.0
    min_lookahead_m: float = 8.0
    max_lookahead_m: float = 28.0
    lookahead_speed_gain: float = 1.1


class AdaptivePurePursuit:
    def __init__(self, config: AdaptivePurePursuitConfig) -> None:
        self.config = config

    def steering(self, frame: TelemetryFrame, path: PreviewPath) -> float:
        if not path.points:
            return 0.0

        lookahead = max(
            self.config.min_lookahead_m,
            min(
                self.config.max_lookahead_m,
                self.config.min_lookahead_m + frame.speed_mps * self.config.lookahead_speed_gain,
            ),
        )

        target = self._find_target_point(frame, path, lookahead)
        dx = target[0] - frame.pose.world_x
        dz = target[1] - frame.pose.world_z

        local_x = math.cos(-frame.pose.yaw_rad) * dx - math.sin(-frame.pose.yaw_rad) * dz
        local_z = math.sin(-frame.pose.yaw_rad) * dx + math.cos(-frame.pose.yaw_rad) * dz

        if abs(local_x) < 1e-6 and abs(local_z) < 1e-6:
            return 0.0

        alpha = math.atan2(local_z, local_x)
        curvature = 2.0 * math.sin(alpha) / max(lookahead, 1e-6)
        steer = self.config.steering_gain * curvature * self.config.wheelbase_m
        return max(-self.config.max_steering_cmd, min(self.config.max_steering_cmd, steer))

    def _find_target_point(self, frame: TelemetryFrame, path: PreviewPath, lookahead_m: float) -> tuple[float, float]:
        acc = 0.0
        prev = (frame.pose.world_x, frame.pose.world_z)
        for point in path.points:
            cur = (point.x, point.z)
            acc += math.dist(prev, cur)
            if acc >= lookahead_m:
                return cur
            prev = cur
        last = path.points[-1]
        return last.x, last.z
