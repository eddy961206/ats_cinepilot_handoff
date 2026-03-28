import cv2
import numpy as np

from ats_cinepilot.perception.lane_observer import LaneObserver, LaneObserverConfig


def test_lane_observer_detects_synthetic_lane_corridor():
    image = np.zeros((720, 1280, 3), dtype=np.uint8)
    cv2.line(image, (460, 719), (600, 420), (255, 255, 255), 10)
    cv2.line(image, (820, 719), (680, 420), (255, 255, 255), 10)

    observer = LaneObserver(LaneObserverConfig())
    result = observer.observe(image)

    assert result.lane_detected is True
    assert result.lane_confidence > 0.5
    assert result.lane_center_x_px is not None
    assert abs(result.lane_offset_px or 0.0) < 120.0


def test_lane_observer_reports_low_confidence_without_lines():
    image = np.zeros((720, 1280, 3), dtype=np.uint8)

    observer = LaneObserver(LaneObserverConfig())
    result = observer.observe(image)

    assert result.lane_detected is False
    assert result.lane_confidence == 0.0
