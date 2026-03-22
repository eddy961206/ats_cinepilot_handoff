from __future__ import annotations

from typing import Any

import cv2

from ats_cinepilot.domain.enums import Mode
from ats_cinepilot.domain.types import MatchedEdge, PreviewPath, RouteHint, SafetyDecision, SpeedTarget, TelemetryFrame


def draw_overlay(
    frame_bgr: Any,
    telemetry: TelemetryFrame | None,
    matched: MatchedEdge | None,
    hint: RouteHint | None,
    path: PreviewPath | None,
    speed_target: SpeedTarget | None,
    safety: SafetyDecision | None,
    mode: Mode,
):
    img = frame_bgr.copy()
    color = (0, 255, 0) if safety and safety.allow_control else (0, 0, 255)
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
    return img
