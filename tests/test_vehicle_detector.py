from ats_cinepilot.perception.observer_types import VehicleDetection
from ats_cinepilot.perception.vehicle_detector import select_lead_vehicle


def test_select_lead_vehicle_prefers_central_largest_vehicle():
    detections = [
        VehicleDetection("car", 0.62, (40, 220, 120, 320), 80.0, 100.0),
        VehicleDetection("truck", 0.81, (520, 240, 760, 520), 240.0, 280.0),
        VehicleDetection("bus", 0.77, (900, 210, 1100, 430), 200.0, 220.0),
    ]

    lead = select_lead_vehicle(detections, frame_width=1280, frame_height=720)

    assert lead is not None
    assert lead.label == "truck"
    assert lead.confidence == 0.81


def test_select_lead_vehicle_returns_none_without_detections():
    assert select_lead_vehicle([], frame_width=1280, frame_height=720) is None
