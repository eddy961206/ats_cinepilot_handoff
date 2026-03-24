import importlib.util
import json
from pathlib import Path


def _load_summary_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "summarize_shadow_log.py"
    spec = importlib.util.spec_from_file_location("summarize_shadow_log", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_summarize_shadow_log_collects_graph_and_safety_metrics(tmp_path):
    module = _load_summary_module()
    log_path = tmp_path / "shadow.jsonl"
    rows = [
        {
            "status": {
                "graph_source": "trucksim_demo_graph_region",
                "alignment_mode": "ats_absolute_identity",
                "pose_source": "authoritative_absolute",
                "pose_frame": "world_absolute",
                "safety_decision": "MATCH_LOST",
                "heading_source": "absolute_position_delta",
                "graph_failure": None,
                "map_match_confidence": 0.95,
                "route_confidence": 0.40,
                "cross_track_error_m": 1.5,
                "nearest_edge_distance_m": 1.4,
                "graph_candidate_count": 16,
            }
        },
        {
            "status": {
                "graph_source": "trucksim_demo_graph_region",
                "alignment_mode": "ats_absolute_identity",
                "pose_source": "authoritative_absolute",
                "pose_frame": "world_absolute",
                "safety_decision": "ROUTE_CONFIDENCE_LOW",
                "heading_source": "absolute_position_hold",
                "graph_failure": None,
                "map_match_confidence": 1.0,
                "route_confidence": 0.49,
                "cross_track_error_m": 0.25,
                "nearest_edge_distance_m": 0.25,
                "graph_candidate_count": 19,
            }
        },
    ]
    log_path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )

    summary = module.summarize_log(log_path)

    assert summary["steps"] == 2
    assert summary["graph_source"] == "trucksim_demo_graph_region"
    assert summary["alignment_mode"] == "ats_absolute_identity"
    assert summary["pose_source"] == "authoritative_absolute"
    assert summary["pose_frame"] == "world_absolute"
    assert summary["first_match_lost_step"] == 1
    assert summary["first_route_confidence_low_step"] == 2
    assert summary["safety_counts"] == {"MATCH_LOST": 1, "ROUTE_CONFIDENCE_LOW": 1}
    assert summary["heading_source_counts"] == {
        "absolute_position_delta": 1,
        "absolute_position_hold": 1,
    }
    assert summary["graph_failure_counts"] == {"None": 2}
    assert summary["match_confidence_min"] == 0.95
    assert summary["match_confidence_max"] == 1.0
    assert summary["graph_candidate_count_min"] == 16
    assert summary["graph_candidate_count_max"] == 19
