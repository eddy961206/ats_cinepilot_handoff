from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from ats_cinepilot.perception.observer_types import LaneObservation, LinePoint


@dataclass(slots=True)
class LaneObserverConfig:
    roi_top_ratio: float = 0.55
    blur_kernel: int = 5
    canny_low: int = 50
    canny_high: int = 150
    hough_threshold: int = 30
    hough_min_line_length: int = 40
    hough_max_line_gap: int = 40
    min_abs_slope: float = 0.35
    line_threshold_value: int = 180


class LaneObserver:
    def __init__(self, config: LaneObserverConfig) -> None:
        self.config = config

    def observe(self, frame_bgr: np.ndarray) -> LaneObservation:
        image = frame_bgr
        if image.ndim == 2:
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        if image.shape[2] == 4:
            image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)

        height, width = image.shape[:2]
        roi_top = int(height * self.config.roi_top_ratio)
        roi = image[roi_top:, :]

        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (self.config.blur_kernel, self.config.blur_kernel), 0)
        _, bright = cv2.threshold(blur, self.config.line_threshold_value, 255, cv2.THRESH_BINARY)
        edges = cv2.Canny(bright, self.config.canny_low, self.config.canny_high)
        lines = cv2.HoughLinesP(
            edges,
            1,
            np.pi / 180,
            threshold=self.config.hough_threshold,
            minLineLength=self.config.hough_min_line_length,
            maxLineGap=self.config.hough_max_line_gap,
        )

        left_segments: list[LinePoint] = []
        right_segments: list[LinePoint] = []
        if lines is not None:
            for line in lines[:, 0]:
                x1, y1, x2, y2 = (int(line[0]), int(line[1]), int(line[2]), int(line[3]))
                dx = x2 - x1
                dy = y2 - y1
                if dx == 0:
                    continue
                slope = dy / dx
                if abs(slope) < self.config.min_abs_slope:
                    continue
                full = (x1, y1 + roi_top, x2, y2 + roi_top)
                if slope < 0:
                    left_segments.append(full)
                else:
                    right_segments.append(full)

        left_line = _average_line(left_segments, height, roi_top)
        right_line = _average_line(right_segments, height, roi_top)
        lane_detected = left_line is not None or right_line is not None
        if not lane_detected:
            return LaneObservation(False, 0.0, None, None, None, None, None, "classical_roi_hough")

        left_bottom_x = left_line[0] if left_line is not None else None
        right_bottom_x = right_line[0] if right_line is not None else None
        if left_bottom_x is not None and right_bottom_x is not None:
            lane_center_x = float((left_bottom_x + right_bottom_x) / 2.0)
            lane_width_px = float(abs(right_bottom_x - left_bottom_x))
        elif left_bottom_x is not None:
            lane_center_x = float(left_bottom_x + width * 0.22)
            lane_width_px = None
        else:
            lane_center_x = float(right_bottom_x - width * 0.22)  # type: ignore[operator]
            lane_width_px = None

        lane_offset_px = lane_center_x - (width / 2.0)
        confidence = 0.0
        if left_line is not None:
            confidence += 0.35
        if right_line is not None:
            confidence += 0.35
        confidence += min(0.30, 0.05 * (len(left_segments) + len(right_segments)))
        confidence = min(1.0, confidence)

        return LaneObservation(
            lane_detected=True,
            lane_confidence=confidence,
            lane_center_x_px=lane_center_x,
            lane_offset_px=lane_offset_px,
            lane_width_px=lane_width_px,
            left_line=left_line,
            right_line=right_line,
            source="classical_roi_hough",
        )


def _average_line(segments: list[LinePoint], y_bottom: int, y_top: int) -> LinePoint | None:
    if not segments:
        return None
    slopes: list[float] = []
    intercepts: list[float] = []
    for x1, y1, x2, y2 in segments:
        if x2 == x1:
            continue
        slope = (y2 - y1) / (x2 - x1)
        intercept = y1 - slope * x1
        slopes.append(slope)
        intercepts.append(intercept)
    if not slopes:
        return None
    slope = float(np.mean(slopes))
    intercept = float(np.mean(intercepts))
    x_bottom = int((y_bottom - intercept) / slope)
    x_top = int((y_top - intercept) / slope)
    return (x_bottom, y_bottom, x_top, y_top)
