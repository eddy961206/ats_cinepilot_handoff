from __future__ import annotations

from typing import Any

import cv2

from ats_cinepilot.domain.enums import Mode
from ats_cinepilot.domain.types import MatchedEdge, PreviewPath, RouteHint, SafetyDecision, SpeedTarget, TelemetryFrame
from ats_cinepilot.perception.observer_types import CvFrameObservation


def draw_overlay(
    frame_bgr: Any,
    telemetry: TelemetryFrame | None,
    matched: MatchedEdge | None,
    hint: RouteHint | None,
    path: PreviewPath | None,
    speed_target: SpeedTarget | None,
    safety: SafetyDecision | None,
    mode: Mode,
    cv_observation: CvFrameObservation | None = None,
    extra_status: dict[str, Any] | None = None,
):
    img = frame_bgr.copy()
    color = (0, 255, 0) if safety and safety.allow_control else (0, 0, 255)
    extra_status = extra_status or {}
    cv2.putText(img, f"mode={mode.name}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
    if telemetry:
        cv2.putText(img, f"speed={telemetry.speed_mps:.2f}m/s", (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
    if matched:
        cv2.putText(
            img,
            f"edge={matched.edge_id} conf={matched.confidence:.2f}",
            (20, 100),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            color,
            2,
        )
    if hint:
        cv2.putText(
            img,
            f"route conf={hint.confidence:.2f} bias={hint.turn_bias:.2f}",
            (20, 130),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            color,
            2,
        )
    if speed_target:
        cv2.putText(
            img,
            f"target={speed_target.target_mps:.2f} reason={speed_target.reason}",
            (20, 160),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            color,
            2,
        )
    if path:
        cv2.putText(
            img,
            f"path points={len(path.points)} path conf={path.confidence:.2f}",
            (20, 190),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            color,
            2,
        )
    if cv_observation is not None:
        lane = cv_observation.lane
        if lane.left_line is not None:
            cv2.line(img, lane.left_line[:2], lane.left_line[2:], (255, 255, 0), 3)
        if lane.right_line is not None:
            cv2.line(img, lane.right_line[:2], lane.right_line[2:], (255, 255, 0), 3)
        if lane.lane_center_x_px is not None:
            center_x = int(lane.lane_center_x_px)
            cv2.line(img, (center_x, img.shape[0]), (center_x, int(img.shape[0] * 0.6)), (0, 200, 255), 2)
        cv2.putText(
            img,
            f"lane detected={lane.lane_detected} conf={lane.lane_confidence:.2f} offset={lane.lane_offset_px}",
            (20, 230),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 200, 255),
            2,
        )
        for det in cv_observation.vehicles:
            left, top, right, bottom = det.box
            cv2.rectangle(img, (left, top), (right, bottom), (255, 0, 255), 2)
            cv2.putText(
                img,
                f"{det.label} {det.confidence:.2f}",
                (left, max(20, top - 8)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 0, 255),
                2,
            )
        if cv_observation.lead_vehicle is not None:
            lead = cv_observation.lead_vehicle
            left, top, right, bottom = lead.box
            cv2.rectangle(img, (left, top), (right, bottom), (0, 165, 255), 3)
            cv2.putText(
                img,
                f"lead {lead.label} {lead.confidence:.2f}",
                (left, min(img.shape[0] - 20, bottom + 20)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 165, 255),
                2,
            )
        cv2.putText(
            img,
            "cv guard={reason} barrier={barrier}".format(
                reason=extra_status.get("cv_guard_reason", "none"),
                barrier=cv_observation.visual_barrier_risk,
            ),
            (20, 260),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 165, 255),
            2,
        )
    return img
