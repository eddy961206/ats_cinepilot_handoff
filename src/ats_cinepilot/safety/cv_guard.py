from __future__ import annotations

from dataclasses import dataclass

from ats_cinepilot.perception.observer_types import CvFrameObservation


@dataclass(slots=True)
class CvGuardConfig:
    enabled: bool = False
    enable_lane_guard: bool = False
    enable_lead_vehicle_guard: bool = True
    min_lane_confidence: float = 0.35
    lead_vehicle_min_confidence: float = 0.60
    lead_vehicle_min_bottom_y_px: float = 560.0
    barrier_guard_enabled: bool = False


@dataclass(slots=True)
class CvGuardDecision:
    triggered: bool
    reason: str | None


def evaluate_cv_guard(
    observation: CvFrameObservation | None,
    config: CvGuardConfig,
) -> CvGuardDecision:
    if not config.enabled or observation is None:
        return CvGuardDecision(False, None)
    if config.enable_lane_guard and observation.lane.lane_confidence < config.min_lane_confidence:
        return CvGuardDecision(True, "lane_confidence_low")
    if (
        config.enable_lead_vehicle_guard
        and
        observation.lead_vehicle is not None
        and observation.lead_vehicle.confidence >= config.lead_vehicle_min_confidence
        and observation.lead_vehicle.bottom_y_px >= config.lead_vehicle_min_bottom_y_px
    ):
        return CvGuardDecision(True, "lead_vehicle_risk")
    if config.barrier_guard_enabled and observation.visual_barrier_risk:
        return CvGuardDecision(True, "barrier_risk")
    return CvGuardDecision(False, None)
