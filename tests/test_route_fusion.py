from ats_cinepilot.route.fusion import compute_route_confidence


def test_route_confidence_is_clamped():
    conf = compute_route_confidence(0.9, 0.8, 0.7, 0.6)
    assert 0.0 <= conf <= 1.0
    assert conf > 0.7
