from __future__ import annotations

from dataclasses import dataclass


LinePoint = tuple[int, int, int, int]
Box = tuple[int, int, int, int]


@dataclass(slots=True)
class LaneObservation:
    lane_detected: bool
    lane_confidence: float
    lane_center_x_px: float | None
    lane_offset_px: float | None
    lane_width_px: float | None
    left_line: LinePoint | None
    right_line: LinePoint | None
    source: str


@dataclass(slots=True)
class VehicleDetection:
    label: str
    confidence: float
    box: Box
    area_px: float
    center_x_px: float


@dataclass(slots=True)
class LeadVehicleObservation:
    label: str
    confidence: float
    box: Box
    area_px: float
    center_x_px: float
    bottom_y_px: float


@dataclass(slots=True)
class CvFrameObservation:
    lane: LaneObservation
    vehicles: list[VehicleDetection]
    lead_vehicle: LeadVehicleObservation | None
    visual_barrier_risk: bool
    overlay_path: str | None
    frame_index: int
