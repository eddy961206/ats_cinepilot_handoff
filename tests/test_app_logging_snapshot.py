from types import SimpleNamespace

from ats_cinepilot.app import _top_candidate_snapshot


def test_top_candidate_snapshot_includes_heading_mode_and_effective_heading_delta():
    candidates = [
        SimpleNamespace(
            edge_id="edge-1",
            distance_m=1.25,
            signed_heading_delta_rad=3.05,
            effective_heading_delta_rad=0.09,
            direction_classification="opposed",
            heading_mode="reverse",
            total_score=2.75,
        )
    ]

    snapshot = _top_candidate_snapshot(candidates)

    assert snapshot == [
        {
            "edge_id": "edge-1",
            "distance_m": 1.25,
            "signed_heading_delta_rad": 3.05,
            "effective_heading_delta_rad": 0.09,
            "direction_classification": "opposed",
            "heading_mode": "reverse",
            "total_score": 2.75,
        }
    ]
