from __future__ import annotations

import math
import struct

from ats_cinepilot.bridge.shared_memory_v2_analysis import rank_axis_candidates
from ats_cinepilot.bridge.shared_memory_v2_analysis import (
    build_candidate_value_summaries,
    build_capture_scenario_summaries,
    build_heading_candidate_summaries,
)


def _build_capture_rows() -> list[dict]:
    rows: list[dict] = []
    for index in range(8):
        t = float(index)
        x = 1000.0 + 0.5 * t * t
        z = 2000.0 + math.sin(t)
        vx = t
        vz = math.cos(t)
        buf = bytearray(1024)
        buf[1:4] = b"ats"
        struct.pack_into("<d", buf, 285, x)
        struct.pack_into("<d", buf, 293, 40.5)
        struct.pack_into("<d", buf, 301, z)
        struct.pack_into("<f", buf, 333, vx)
        struct.pack_into("<f", buf, 357, vz)
        struct.pack_into("<f", buf, 445, math.hypot(vx, vz))
        rows.append(
            {
                "mono_time_s": t,
                "raw": bytes(buf),
                "velocity_x_mps": vx,
                "velocity_z_mps": vz,
            }
        )
    return rows


def test_rank_axis_candidates_prefers_authoritative_absolute_offsets():
    rows = _build_capture_rows()

    x_candidates = rank_axis_candidates(rows, axis="x", top_n=3)
    z_candidates = rank_axis_candidates(rows, axis="z", top_n=3)

    assert x_candidates[0].offset == 285
    assert x_candidates[0].value_format == "f64"
    assert z_candidates[0].offset == 301
    assert z_candidates[0].value_format == "f64"


def test_build_capture_scenario_summaries_reports_heading_and_reset_counts():
    samples = [
        {
            "label": "reverse",
            "speed_mps": 0.0,
            "pose_world_x": 0.0,
            "pose_world_z": 0.0,
            "heading_source": "velocity_direction",
            "anchor_heading_locked": False,
            "discontinuity_detected": False,
            "discontinuity_distance_m": None,
        },
        {
            "label": "reverse",
            "speed_mps": 1.0,
            "pose_world_x": 1.0,
            "pose_world_z": 0.0,
            "heading_source": "absolute_position_delta",
            "anchor_heading_locked": True,
            "discontinuity_detected": False,
            "discontinuity_distance_m": None,
        },
        {
            "label": "teleport_recover",
            "speed_mps": 0.0,
            "pose_world_x": 0.0,
            "pose_world_z": 0.0,
            "heading_source": "velocity_direction",
            "anchor_heading_locked": False,
            "discontinuity_detected": True,
            "discontinuity_distance_m": 120.0,
        },
    ]

    summaries = build_capture_scenario_summaries(samples)

    reverse = next(row for row in summaries if row["label"] == "reverse")
    teleport = next(row for row in summaries if row["label"] == "teleport_recover")

    assert reverse["sample_count"] == 2
    assert reverse["heading_source_absolute_position_delta"] == 1
    assert reverse["heading_source_velocity_direction"] == 1
    assert reverse["anchor_locked_samples"] == 1
    assert reverse["pose_delta_max_m"] == 1.0
    assert teleport["discontinuity_count"] == 1
    assert teleport["discontinuity_max_distance_m"] == 120.0


def test_build_candidate_value_summaries_reports_span_by_label():
    samples = []
    for index, value in enumerate((0.2, 0.3, 0.6)):
        buf = bytearray(16)
        struct.pack_into("<f", buf, 4, value)
        samples.append({"label": "left_turn", "raw": bytes(buf), "sample_index": index})

    summaries = build_candidate_value_summaries(samples, specs=[(4, "f32")])

    assert summaries == [
        {
            "label": "left_turn",
            "offset": 4,
            "value_format": "f32",
            "sample_count": 3,
            "first": 0.2,
            "last": 0.6,
            "minimum": 0.2,
            "maximum": 0.6,
            "span": 0.4,
            "mean_abs_step": 0.2,
        }
    ]


def test_build_heading_candidate_summaries_reports_pose_yaw_correlation():
    samples = []
    for index, yaw in enumerate((0.0, 0.1, 0.2, 0.3)):
        buf = bytearray(16)
        struct.pack_into("<f", buf, 4, -0.5 * yaw + 0.2)
        samples.append(
            {
                "label": "slow_right_turn",
                "raw": bytes(buf),
                "speed_mps": 1.0,
                "pose_yaw_rad": yaw,
            }
        )

    summaries = build_heading_candidate_summaries(samples, specs=[(4, "f32")], min_speed_mps=0.2)

    assert summaries == [
        {
            "label": "slow_right_turn",
            "offset": 4,
            "value_format": "f32",
            "sample_count": 4,
            "moving_sample_count": 4,
            "first": 0.2,
            "last": 0.05,
            "minimum": 0.05,
            "maximum": 0.2,
            "span": 0.15,
            "mean_abs_step": 0.05,
            "corr_with_pose_yaw": -1.0,
        }
    ]
