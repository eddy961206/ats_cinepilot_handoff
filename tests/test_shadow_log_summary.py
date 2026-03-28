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


def test_summarize_shadow_log_collects_direction_counts_and_handles_missing_fields(tmp_path):
    module = _load_summary_module()
    log_path = tmp_path / "shadow_direction.jsonl"
    rows = [
        {
            "status": {
                "graph_source": "trucksim_dense_local_region",
                "alignment_mode": "ats_absolute_identity",
                "pose_source": "authoritative_absolute",
                "pose_frame": "world_absolute",
                "safety_decision": "NONE",
                "heading_source": "absolute_position_delta",
                "graph_failure": None,
                "map_match_confidence": 0.91,
                "route_confidence": 0.62,
                "cross_track_error_m": 0.9,
                "nearest_edge_distance_m": 0.4,
                "graph_candidate_count": 4,
                "selected_edge_id": 101,
                "selected_reason": "heading",
                "direction_confidence_state": "confident",
                "selected_score_breakdown": {
                    "distance_score": 0.91,
                    "heading_score": 0.85,
                    "continuity_bonus": 0.10,
                },
                "top_candidates": [
                    {
                        "edge_id": 101,
                        "distance_m": 0.4,
                        "signed_heading_delta_rad": 0.12,
                        "direction_classification": "aligned",
                        "total_score": 0.93,
                    },
                    {
                        "edge_id": 202,
                        "distance_m": 0.7,
                        "signed_heading_delta_rad": 2.9,
                        "direction_classification": "opposed",
                        "total_score": 0.35,
                    },
                ],
            }
        },
        {
            "status": {
                "graph_source": "trucksim_dense_local_region",
                "alignment_mode": "ats_absolute_identity",
                "pose_source": "authoritative_absolute",
                "pose_frame": "world_absolute",
                "safety_decision": "MATCH_LOST",
                "heading_source": "absolute_position_hold",
                "graph_failure": "direction_ambiguous",
                "map_match_confidence": 0.64,
                "route_confidence": 0.55,
                "cross_track_error_m": 2.1,
                "nearest_edge_distance_m": 1.8,
                "graph_candidate_count": 3,
                "selected_edge_id": 303,
                "selected_reason": "continuity",
                "direction_confidence_state": "ambiguous",
                "selected_score_breakdown": {
                    "distance_score": 0.72,
                    "heading_score": 0.41,
                    "continuity_bonus": 0.30,
                },
            }
        },
        {
            "status": {
                "graph_source": "trucksim_dense_local_region",
                "alignment_mode": "ats_absolute_identity",
                "pose_source": "authoritative_absolute",
                "pose_frame": "world_absolute",
                "safety_decision": "NONE",
                "heading_source": "absolute_position_hold",
                "graph_failure": None,
                "map_match_confidence": 0.88,
                "route_confidence": 0.58,
                "cross_track_error_m": 1.1,
                "nearest_edge_distance_m": 0.6,
                "graph_candidate_count": 2,
            }
        },
    ]
    log_path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )

    summary = module.summarize_log(log_path)

    assert summary["steps"] == 3
    assert summary["selected_reason_counts"] == {
        "heading": 1,
        "continuity": 1,
    }
    assert summary["direction_confidence_state_counts"] == {
        "confident": 1,
        "ambiguous": 1,
    }


def test_summarize_shadow_log_collects_demo_command_metrics(tmp_path):
    module = _load_summary_module()
    log_path = tmp_path / "demo_active_curve.jsonl"
    rows = [
        {
            "command": {
                "steering": 0.00,
                "throttle": 0.35,
                "brake": 0.00,
            },
            "status": {
                "graph_source": "toy_gentle_curve_graph",
                "alignment_mode": "anchored_local_toy_graph",
                "pose_source": "authoritative_absolute",
                "pose_frame": "anchored_local",
                "safety_decision": "NONE",
                "heading_source": "absolute_position_delta",
                "graph_failure": None,
                "map_match_confidence": 1.0,
                "route_confidence": 0.70,
                "cross_track_error_m": 0.02,
                "nearest_edge_distance_m": 0.02,
                "graph_candidate_count": 1,
                "demo_guard_reason": "bootstrap",
            },
        },
        {
            "command": {
                "steering": 0.18,
                "throttle": 0.28,
                "brake": 0.00,
            },
            "status": {
                "graph_source": "toy_gentle_curve_graph",
                "alignment_mode": "anchored_local_toy_graph",
                "pose_source": "authoritative_absolute",
                "pose_frame": "anchored_local",
                "safety_decision": "NONE",
                "heading_source": "absolute_position_delta",
                "graph_failure": None,
                "map_match_confidence": 1.0,
                "route_confidence": 0.70,
                "cross_track_error_m": 0.05,
                "nearest_edge_distance_m": 0.05,
                "graph_candidate_count": 1,
                "demo_guard_reason": "armed",
            },
        },
        {
            "command": {
                "steering": 0.22,
                "throttle": 0.00,
                "brake": 0.31,
            },
            "status": {
                "graph_source": "toy_gentle_curve_graph",
                "alignment_mode": "anchored_local_toy_graph",
                "pose_source": "authoritative_absolute",
                "pose_frame": "anchored_local",
                "safety_decision": "DEMO_GUARD",
                "heading_source": "absolute_position_hold",
                "graph_failure": None,
                "map_match_confidence": 1.0,
                "route_confidence": 0.70,
                "cross_track_error_m": 0.08,
                "nearest_edge_distance_m": 0.08,
                "graph_candidate_count": 1,
                "demo_guard_reason": "speed_cap_exceeded",
            },
        },
    ]
    log_path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )

    summary = module.summarize_log(log_path)

    assert summary["steering_abs_max"] == 0.22
    assert summary["non_trivial_steering_count"] == 2
    assert summary["throttle_command_count"] == 2
    assert summary["brake_command_count"] == 1
    assert summary["demo_guard_reason_counts"] == {
        "bootstrap": 1,
        "armed": 1,
        "speed_cap_exceeded": 1,
    }


def test_summarize_shadow_log_tracks_dense_corridor_edge_sequence_metrics(tmp_path):
    module = _load_summary_module()
    log_path = tmp_path / "dense_demo.jsonl"
    rows = [
        {
            "matched": {"edge_id": "edge_a"},
            "command": {"steering": 0.00, "throttle": 0.2, "brake": 0.0},
            "status": {
                "graph_source": "curated_dense_local_corridor_graph",
                "alignment_mode": "ats_absolute_identity",
                "pose_source": "authoritative_absolute",
                "pose_frame": "world_absolute",
                "safety_decision": "NONE",
                "heading_source": "absolute_position_hold",
                "graph_failure": None,
                "map_match_confidence": 1.0,
                "route_confidence": 0.7,
                "cross_track_error_m": 0.02,
                "nearest_edge_distance_m": 0.04,
                "graph_candidate_count": 1,
                "demo_corridor_current_index": 0,
                "demo_corridor_highest_index": 0,
            },
        },
        {
            "matched": {"edge_id": "edge_b"},
            "command": {"steering": 0.11, "throttle": 0.2, "brake": 0.0},
            "status": {
                "graph_source": "curated_dense_local_corridor_graph",
                "alignment_mode": "ats_absolute_identity",
                "pose_source": "authoritative_absolute",
                "pose_frame": "world_absolute",
                "safety_decision": "NONE",
                "heading_source": "absolute_position_delta",
                "graph_failure": None,
                "map_match_confidence": 1.0,
                "route_confidence": 0.7,
                "cross_track_error_m": 0.04,
                "nearest_edge_distance_m": 0.05,
                "graph_candidate_count": 1,
                "demo_corridor_current_index": 1,
                "demo_corridor_highest_index": 1,
            },
        },
    ]
    log_path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )

    summary = module.summarize_log(log_path)

    assert summary["corridor_edge_sequence"] == ["edge_a", "edge_b"]
    assert summary["corridor_highest_index"] == 1
