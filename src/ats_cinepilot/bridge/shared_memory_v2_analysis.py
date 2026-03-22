from __future__ import annotations

import math
import struct
from dataclasses import dataclass


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
