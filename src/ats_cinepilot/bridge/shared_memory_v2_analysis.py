from __future__ import annotations

import math
import struct
from dataclasses import dataclass
from itertools import groupby


@dataclass(slots=True)
class AxisCandidate:
    offset: int
    value_format: str
    correlation: float
    slope: float
    span: float


def rank_axis_candidates(rows: list[dict], axis: str, top_n: int = 10) -> list[AxisCandidate]:
    if axis not in {"x", "z"}:
        raise ValueError(f"unsupported axis: {axis}")
    if len(rows) < 3:
        return []

    raws = [bytes(row["raw"]) for row in rows]
    times = [float(row["mono_time_s"]) for row in rows]
    velocity_key = "velocity_x_mps" if axis == "x" else "velocity_z_mps"
    target = [float(row[velocity_key]) for row in rows[1:]]
    candidates: list[AxisCandidate] = []

    for value_format, size in (("f32", 4), ("f64", 8)):
        for offset in range(0, len(raws[0]) - size + 1):
            values = _read_series(raws, offset, value_format)
            if values is None:
                continue
            span = max(values) - min(values)
            if abs(span) < 0.05:
                continue
            deriv = _differentiate(values, times)
            if len(deriv) != len(target):
                continue
            correlation = _correlation(deriv, target)
            if abs(correlation) < 0.8:
                continue
            slope = _slope(target, deriv)
            candidates.append(
                AxisCandidate(
                    offset=offset,
                    value_format=value_format,
                    correlation=correlation,
                    slope=slope,
                    span=span,
                )
            )

    return sorted(
        candidates,
        key=lambda row: (
            abs(row.correlation),
            -abs(abs(row.slope) - 1.0),
            abs(row.span),
        ),
        reverse=True,
    )[:top_n]


def build_capture_scenario_summaries(samples: list[dict]) -> list[dict]:
    rows = sorted(samples, key=lambda row: str(row.get("label", "")))
    summaries: list[dict] = []
    for label, group_iter in groupby(rows, key=lambda row: str(row.get("label", ""))):
        group = list(group_iter)
        speeds = [float(row.get("speed_mps", 0.0) or 0.0) for row in group]
        pose_deltas = _compute_pose_deltas(group)
        discontinuity_distances = [
            float(row["discontinuity_distance_m"])
            for row in group
            if row.get("discontinuity_detected") and row.get("discontinuity_distance_m") is not None
        ]
        heading_sources: dict[str, int] = {}
        for row in group:
            source = str(row.get("heading_source", "unknown") or "unknown")
            heading_sources[source] = heading_sources.get(source, 0) + 1
        summary = {
            "label": label,
            "sample_count": len(group),
            "speed_min_mps": _round6(min(speeds) if speeds else 0.0),
            "speed_max_mps": _round6(max(speeds) if speeds else 0.0),
            "speed_mean_mps": _round6(sum(speeds) / len(speeds) if speeds else 0.0),
            "pose_delta_max_m": _round6(max(pose_deltas) if pose_deltas else 0.0),
            "pose_delta_mean_m": _round6(sum(pose_deltas) / len(pose_deltas) if pose_deltas else 0.0),
            "anchor_locked_samples": sum(1 for row in group if row.get("anchor_heading_locked")),
            "discontinuity_count": sum(1 for row in group if row.get("discontinuity_detected")),
            "discontinuity_max_distance_m": _round6(max(discontinuity_distances) if discontinuity_distances else 0.0),
        }
        for key in (
            "absolute_position_delta",
            "absolute_position_hold",
            "velocity_direction",
            "unknown",
        ):
            summary[f"heading_source_{key}"] = heading_sources.get(key, 0)
        summaries.append(summary)
    return summaries


def build_candidate_value_summaries(samples: list[dict], specs: list[tuple[int, str]]) -> list[dict]:
    rows = sorted(samples, key=lambda row: str(row.get("label", "")))
    out: list[dict] = []
    for label, group_iter in groupby(rows, key=lambda row: str(row.get("label", ""))):
        group = list(group_iter)
        for offset, value_format in specs:
            values = [_read_value(bytes(row["raw"]), offset, value_format) for row in group]
            steps = [abs(values[index] - values[index - 1]) for index in range(1, len(values))]
            out.append(
                {
                    "label": label,
                    "offset": offset,
                    "value_format": value_format,
                    "sample_count": len(values),
                    "first": _round6(values[0]),
                    "last": _round6(values[-1]),
                    "minimum": _round6(min(values)),
                    "maximum": _round6(max(values)),
                    "span": _round6(max(values) - min(values)),
                    "mean_abs_step": _round6(sum(steps) / len(steps) if steps else 0.0),
                }
            )
    return out


def build_heading_candidate_summaries(
    samples: list[dict],
    specs: list[tuple[int, str]],
    *,
    min_speed_mps: float = 0.2,
) -> list[dict]:
    rows = sorted(samples, key=lambda row: str(row.get("label", "")))
    out: list[dict] = []
    for label, group_iter in groupby(rows, key=lambda row: str(row.get("label", ""))):
        group = list(group_iter)
        moving = [row for row in group if float(row.get("speed_mps", 0.0) or 0.0) >= min_speed_mps]
        for offset, value_format in specs:
            values = [_read_value(bytes(row["raw"]), offset, value_format) for row in group]
            steps = [abs(values[index] - values[index - 1]) for index in range(1, len(values))]
            moving_values = [_read_value(bytes(row["raw"]), offset, value_format) for row in moving]
            moving_yaws = [float(row.get("pose_yaw_rad", 0.0) or 0.0) for row in moving]
            out.append(
                {
                    "label": label,
                    "offset": offset,
                    "value_format": value_format,
                    "sample_count": len(values),
                    "moving_sample_count": len(moving_values),
                    "first": _round6(values[0]),
                    "last": _round6(values[-1]),
                    "minimum": _round6(min(values)),
                    "maximum": _round6(max(values)),
                    "span": _round6(max(values) - min(values)),
                    "mean_abs_step": _round6(sum(steps) / len(steps) if steps else 0.0),
                    "corr_with_pose_yaw": _round6(_correlation(moving_values, moving_yaws)) if moving_values else 0.0,
                }
            )
    return out


def _read_series(raws: list[bytes], offset: int, value_format: str) -> list[float] | None:
    values: list[float] = []
    fmt = "<f" if value_format == "f32" else "<d"
    limit = 1.0e9
    for raw in raws:
        value = struct.unpack_from(fmt, raw, offset)[0]
        if not math.isfinite(value) or abs(value) > limit:
            return None
        values.append(float(value))
    return values


def _differentiate(values: list[float], times: list[float]) -> list[float]:
    out: list[float] = []
    for index in range(1, len(values)):
        dt = times[index] - times[index - 1]
        if dt <= 0.0:
            out.append(0.0)
            continue
        out.append((values[index] - values[index - 1]) / dt)
    return out


def _correlation(left: list[float], right: list[float]) -> float:
    if len(left) != len(right) or len(left) < 2:
        return 0.0
    left_mean = sum(left) / len(left)
    right_mean = sum(right) / len(right)
    left_var = sum((value - left_mean) ** 2 for value in left)
    right_var = sum((value - right_mean) ** 2 for value in right)
    if left_var <= 1.0e-12 or right_var <= 1.0e-12:
        return 0.0
    covariance = sum((lx - left_mean) * (rx - right_mean) for lx, rx in zip(left, right))
    return covariance / math.sqrt(left_var * right_var)


def _slope(left: list[float], right: list[float]) -> float:
    if len(left) != len(right) or len(left) < 2:
        return 0.0
    left_mean = sum(left) / len(left)
    denominator = sum((value - left_mean) ** 2 for value in left)
    if denominator <= 1.0e-12:
        return 0.0
    right_mean = sum(right) / len(right)
    numerator = sum((lx - left_mean) * (rx - right_mean) for lx, rx in zip(left, right))
    return numerator / denominator


def _compute_pose_deltas(samples: list[dict]) -> list[float]:
    deltas: list[float] = []
    for index in range(1, len(samples)):
        ax = float(samples[index - 1].get("pose_world_x", 0.0) or 0.0)
        az = float(samples[index - 1].get("pose_world_z", 0.0) or 0.0)
        bx = float(samples[index].get("pose_world_x", 0.0) or 0.0)
        bz = float(samples[index].get("pose_world_z", 0.0) or 0.0)
        deltas.append(math.hypot(bx - ax, bz - az))
    return deltas


def _read_value(raw: bytes, offset: int, value_format: str) -> float:
    if value_format == "f64":
        return float(struct.unpack_from("<d", raw, offset)[0])
    if value_format == "f32":
        return float(struct.unpack_from("<f", raw, offset)[0])
    raise ValueError(f"unsupported format: {value_format}")


def _round6(value: float) -> float:
    return round(float(value), 6)
