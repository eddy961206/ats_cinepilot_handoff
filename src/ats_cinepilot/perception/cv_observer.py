from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import cv2

from ats_cinepilot.ops.artifacts import CvArtifactWriter
from ats_cinepilot.perception.lane_observer import LaneObserver, LaneObserverConfig
from ats_cinepilot.perception.observer_types import CvFrameObservation, LaneObservation
from ats_cinepilot.perception.vehicle_detector import (
    VehicleDetector,
    VehicleDetectorConfig,
    select_lead_vehicle,
)
from ats_cinepilot.ui.overlay import draw_overlay


@dataclass(slots=True)
class CvObserverConfig:
    enabled: bool = False
    lane_enabled: bool = True
    vehicles_enabled: bool = True
    barrier_enabled: bool = False
    show_window: bool = False
    save_video: bool = True
    save_frames: bool = False
    artifact_dir: str = "data/artifacts/cv/default"
    summary_jsonl_path: str | None = None


class CvObserver:
    def __init__(
        self,
        config: CvObserverConfig,
        *,
        lane_config: LaneObserverConfig | None = None,
        vehicle_config: VehicleDetectorConfig | None = None,
    ) -> None:
        self.config = config
        self.lane_observer = LaneObserver(lane_config or LaneObserverConfig()) if config.lane_enabled else None
        self.vehicle_detector = (
            VehicleDetector(vehicle_config or VehicleDetectorConfig())
            if config.vehicles_enabled
            else None
        )
        self.writer = CvArtifactWriter(
            artifact_dir=config.artifact_dir,
            save_video=config.save_video,
            save_frames=config.save_frames,
            summary_jsonl_path=config.summary_jsonl_path,
        )

    def analyze(self, frame_bgr, *, frame_index: int) -> CvFrameObservation:
        lane = (
            self.lane_observer.observe(frame_bgr)
            if self.lane_observer is not None
            else LaneObservation(False, 0.0, None, None, None, None, None, "disabled")
        )
        vehicles = self.vehicle_detector.detect(frame_bgr) if self.vehicle_detector is not None else []
        lead = select_lead_vehicle(
            vehicles,
            frame_width=frame_bgr.shape[1],
            frame_height=frame_bgr.shape[0],
        )
        return CvFrameObservation(
            lane=lane,
            vehicles=vehicles,
            lead_vehicle=lead,
            visual_barrier_risk=False,
            overlay_path=None,
            frame_index=frame_index,
        )

    def publish(
        self,
        frame_bgr,
        *,
        observation: CvFrameObservation,
        telemetry,
        matched,
        hint,
        path,
        speed_target,
        safety,
        mode,
        extra_status: dict[str, Any] | None = None,
    ) -> CvFrameObservation:
        overlay = draw_overlay(
            frame_bgr,
            telemetry,
            matched,
            hint,
            path,
            speed_target,
            safety,
            mode,
            cv_observation=observation,
            extra_status=extra_status or {},
        )
        overlay_path = self.writer.write(
            frame_index=observation.frame_index,
            overlay_bgr=overlay,
            summary=_observation_to_summary(observation, extra_status or {}),
        )
        if self.config.show_window:
            cv2.imshow("ats-cinepilot-cv", overlay)
            cv2.waitKey(1)
        observation.overlay_path = overlay_path
        return observation

    def close(self) -> None:
        self.writer.close()
        if self.config.show_window:
            cv2.destroyWindow("ats-cinepilot-cv")


def _observation_to_summary(observation: CvFrameObservation, extra_status: dict[str, Any]) -> dict[str, Any]:
    lead = observation.lead_vehicle
    return {
        "frame_index": observation.frame_index,
        "lane_detected": observation.lane.lane_detected,
        "lane_confidence": observation.lane.lane_confidence,
        "lane_center_x_px": observation.lane.lane_center_x_px,
        "lane_offset_px": observation.lane.lane_offset_px,
        "lead_vehicle_detected": lead is not None,
        "lead_vehicle_confidence": lead.confidence if lead else 0.0,
        "lead_vehicle_box": lead.box if lead else None,
        "visual_barrier_risk": observation.visual_barrier_risk,
        "cv_guard_reason": extra_status.get("cv_guard_reason"),
    }
