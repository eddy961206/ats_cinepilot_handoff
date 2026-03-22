from __future__ import annotations

from typing import Any, Optional, Protocol, Sequence

from .types import (
    MatchedEdge,
    Pose2D,
    PreviewPath,
    RouteHint,
    SafetyDecision,
    SpeedTarget,
    TelemetryFrame,
    VehicleCommand,
)


class TelemetrySource(Protocol):
    def connect(self) -> None: ...
    def read(self) -> Optional[TelemetryFrame]: ...
    def is_healthy(self) -> bool: ...


class ControlSink(Protocol):
    def connect(self) -> None: ...
    def apply(self, command: VehicleCommand) -> None: ...
    def neutralize(self) -> None: ...
    def is_healthy(self) -> bool: ...


class ManualOverrideSource(Protocol):
    def poll_override(self) -> bool: ...


class CaptureSource(Protocol):
    def start(self) -> None: ...
    def grab(self) -> Any: ...
    def stop(self) -> None: ...


class MapRepository(Protocol):
    def load(self, profile_name: str) -> None: ...
    def nearby_edges(self, pose: Pose2D, radius_m: float) -> Sequence[str]: ...
    def edge_geometry(self, edge_id: str) -> Any: ...


class PoseMatcher(Protocol):
    def match(
        self,
        frame: TelemetryFrame,
        previous: Optional[MatchedEdge],
    ) -> Optional[MatchedEdge]: ...


class RouteProvider(Protocol):
    def get_hint(
        self,
        frame: TelemetryFrame,
        matched: Optional[MatchedEdge],
    ) -> RouteHint: ...


class PreviewPlanner(Protocol):
    def build_path(
        self,
        frame: TelemetryFrame,
        matched: MatchedEdge,
        hint: RouteHint,
    ) -> PreviewPath: ...


class SpeedPlanner(Protocol):
    def compute(
        self,
        frame: TelemetryFrame,
        path: PreviewPath,
    ) -> SpeedTarget: ...


class LateralController(Protocol):
    def steering(
        self,
        frame: TelemetryFrame,
        path: PreviewPath,
    ) -> float: ...


class LongitudinalController(Protocol):
    def command(
        self,
        frame: TelemetryFrame,
        target: SpeedTarget,
    ) -> tuple[float, float]: ...


class SafetyPolicy(Protocol):
    def evaluate(
        self,
        frame: Optional[TelemetryFrame],
        matched: Optional[MatchedEdge],
        hint: Optional[RouteHint],
        path: Optional[PreviewPath],
        command: Optional[VehicleCommand],
    ) -> SafetyDecision: ...
