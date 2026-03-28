from ats_cinepilot.perception.observer_types import CvFrameObservation, LaneObservation, LeadVehicleObservation
from ats_cinepilot.safety.cv_guard import CvGuardConfig, evaluate_cv_guard


def test_cv_guard_rejects_low_lane_confidence():
    observation = CvFrameObservation(
        lane=LaneObservation(
            lane_detected=False,
            lane_confidence=0.12,
            lane_center_x_px=None,
            lane_offset_px=None,
            lane_width_px=None,
            left_line=None,
            right_line=None,
            source="classical_roi_hough",
        ),
        vehicles=[],
        lead_vehicle=None,
        visual_barrier_risk=False,
        overlay_path=None,
        frame_index=1,
    )

    guard = evaluate_cv_guard(
        observation,
        CvGuardConfig(enabled=True, enable_lane_guard=True, min_lane_confidence=0.35),
    )

    assert guard.triggered is True
    assert guard.reason == "lane_confidence_low"


def test_cv_guard_rejects_risky_lead_vehicle():
    observation = CvFrameObservation(
        lane=LaneObservation(
            lane_detected=True,
            lane_confidence=0.8,
            lane_center_x_px=640.0,
            lane_offset_px=0.0,
            lane_width_px=320.0,
            left_line=None,
            right_line=None,
            source="classical_roi_hough",
        ),
        vehicles=[],
        lead_vehicle=LeadVehicleObservation(
            label="truck",
            confidence=0.84,
            box=(500, 260, 760, 620),
            area_px=93600.0,
            center_x_px=630.0,
            bottom_y_px=620.0,
        ),
        visual_barrier_risk=False,
        overlay_path=None,
        frame_index=2,
    )

    guard = evaluate_cv_guard(
        observation,
        CvGuardConfig(enabled=True, lead_vehicle_min_confidence=0.5, lead_vehicle_min_bottom_y_px=580),
    )

    assert guard.triggered is True
    assert guard.reason == "lead_vehicle_risk"
