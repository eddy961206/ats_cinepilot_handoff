from scripts.fit_demo_dense_corridor import build_runtime_demo_thresholds


def test_build_runtime_demo_thresholds_respects_more_conservative_bootstrap_config():
    cfg = {
        "demo": {
            "bootstrap_max_speed_mps": 0.4,
            "bootstrap_throttle": 0.25,
            "bootstrap_min_match_confidence": 0.85,
            "bootstrap_max_cross_track_error_m": 0.3,
            "bootstrap_max_nearest_edge_distance_m": 0.2,
        }
    }

    payload = build_runtime_demo_thresholds(cfg)

    assert payload["bootstrap_max_speed_mps"] == 0.4
    assert payload["bootstrap_throttle"] == 0.25
    assert payload["bootstrap_min_match_confidence"] == 0.85
    assert payload["bootstrap_max_cross_track_error_m"] == 0.3
    assert payload["bootstrap_max_nearest_edge_distance_m"] == 0.2
