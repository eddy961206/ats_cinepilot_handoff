from __future__ import annotations

import math
import struct

from ats_cinepilot.bridge.shared_memory_v2_analysis import rank_axis_candidates


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
