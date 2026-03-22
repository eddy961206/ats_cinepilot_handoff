from __future__ import annotations

import math
from dataclasses import dataclass

from ats_cinepilot.domain.types import PreviewPath, SpeedTarget, TelemetryFrame


@dataclass
class SpeedPlannerConfig:
    max_lateral_accel_mps2: float = 1.8
    curve_speed_floor_mps: float = 8.0
    junction_speed_cap_mps: float = 14.0
    user_speed_cap_mps: float = 25.0


class SpeedPlanner:
    def __init__(self, config: SpeedPlannerConfig) -> None:
        self.config = config

    def compute(self, frame: TelemetryFrame, path: PreviewPath) -> SpeedTarget:
        limit_cap = frame.speed_limit_mps if frame.speed_limit_mps is not None else self.config.user_speed_cap_mps
        curve_cap = self._curve_speed_cap(path)
        target = min(limit_cap, curve_cap, self.config.user_speed_cap_mps)
        reason = "limit"
        if target == curve_cap and curve_cap < limit_cap:
            reason = "curve"
        return SpeedTarget(target_mps=target, hard_cap_mps=min(limit_cap, self.config.user_speed_cap_mps), reason=reason)

    def _curve_speed_cap(self, path: PreviewPath) -> float:
        max_curv = 0.0
        for point in path.points[:30]:
            max_curv = max(max_curv, point.curvature)
        if max_curv <= 1e-6:
            return self.config.user_speed_cap_mps
        cap = math.sqrt(self.config.max_lateral_accel_mps2 / max_curv)
        return max(self.config.curve_speed_floor_mps, min(cap, self.config.user_speed_cap_mps))
