from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional, Sequence


@dataclass(slots=True)
class Pose2D:
    world_x: float
    world_z: float
    yaw_rad: float


@dataclass(slots=True)
class TelemetryFrame:
    mono_time_s: float
    game_tick: int
    paused: bool
    speed_mps: float
    speed_limit_mps: Optional[float]
    nav_distance_m: Optional[float]
    pose: Pose2D

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class MatchedEdge:
    edge_id: str
    lane_id: Optional[str]
    progress_m: float
    cross_track_error_m: float
    heading_error_rad: float
    confidence: float


@dataclass(slots=True)
class RouteHint:
    source: str
    turn_bias: float
    path_overlap: float
    next_branch_id: Optional[str]
    confidence: float


@dataclass(slots=True)
class PreviewPoint:
    x: float
    z: float
    curvature: float
    speed_cap_mps: float


@dataclass(slots=True)
class PreviewPath:
    points: Sequence[PreviewPoint]
    horizon_m: float
    branch_id: Optional[str]
    confidence: float


@dataclass(slots=True)
class SpeedTarget:
    target_mps: float
    hard_cap_mps: float
    reason: str


@dataclass(slots=True)
class VehicleCommand:
    steering: float
    throttle: float
    brake: float
    left_blinker: bool = False
    right_blinker: bool = False
    cruise_enable: bool = False

    def clipped(self) -> "VehicleCommand":
        return VehicleCommand(
            steering=max(-1.0, min(1.0, self.steering)),
            throttle=max(0.0, min(1.0, self.throttle)),
            brake=max(0.0, min(1.0, self.brake)),
            left_blinker=self.left_blinker,
            right_blinker=self.right_blinker,
            cruise_enable=self.cruise_enable,
        )


@dataclass(slots=True)
class SafetyDecision:
    allow_control: bool
    reason: Any
    neutral_command: VehicleCommand = field(
        default_factory=lambda: VehicleCommand(0.0, 0.0, 0.0)
    )
