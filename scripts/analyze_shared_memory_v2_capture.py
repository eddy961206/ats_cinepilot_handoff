from __future__ import annotations

import argparse
import base64
import csv
import json
import struct
from pathlib import Path

from ats_cinepilot.bridge.shared_memory_v2_analysis import (
    build_candidate_value_summaries,
    build_capture_scenario_summaries,
    build_heading_candidate_summaries,
    rank_axis_candidates,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", action="append", required=True, help="Capture jsonl file or directory. Can repeat.")
    parser.add_argument("--top", type=int, default=8)
    parser.add_argument("--inspect", action="append", default=[], help="Offset spec like 285:f64")
    parser.add_argument("--summary-json", default="")
    parser.add_argument("--scenario-summary-csv", default="")
    parser.add_argument("--candidate-summary-csv", default="")
    parser.add_argument("--heading-summary-csv", default="")
    args = parser.parse_args()

    rows = _load_capture_rows(args.input)
    if not rows:
        raise SystemExit("no capture samples found")

    print(f"loaded {len(rows)} samples")
    labels = sorted({row.get('label', '') for row in rows})
    print(f"labels: {labels}")

    x_candidates = rank_axis_candidates(rows, axis="x", top_n=args.top)
    z_candidates = rank_axis_candidates(rows, axis="z", top_n=args.top)

    print("top x-axis candidates:")
    for row in x_candidates:
        print(
            f"  - offset={row.offset} format={row.value_format} "
            f"corr={row.correlation:.4f} slope={row.slope:.4f} span={row.span:.4f}"
        )

    print("top z-axis candidates:")
    for row in z_candidates:
        print(
            f"  - offset={row.offset} format={row.value_format} "
            f"corr={row.correlation:.4f} slope={row.slope:.4f} span={row.span:.4f}"
        )

    scenario_summaries = build_capture_scenario_summaries(rows)
    if scenario_summaries:
        print("scenario summaries:")
        for row in scenario_summaries:
            print(
                "  - {label}: samples={sample_count} speed={speed_min_mps:.3f}..{speed_max_mps:.3f} "
                "pose_delta_max={pose_delta_max_m:.3f} heading(delta/hold/vel)={heading_source_absolute_position_delta}/{heading_source_absolute_position_hold}/{heading_source_velocity_direction} "
                "anchor_locked={anchor_locked_samples} discontinuities={discontinuity_count}".format(
                    **row,
                )
            )

    inspect_specs = [(int(spec.split(":", maxsplit=1)[0]), spec.split(":", maxsplit=1)[1]) for spec in args.inspect]
    for spec in args.inspect:
        offset_str, value_format = spec.split(":", maxsplit=1)
        offset = int(offset_str)
        series = [_read_value(row["raw"], offset, value_format) for row in rows]
        print(f"inspect {spec}: first={series[0]:.6f} last={series[-1]:.6f} min={min(series):.6f} max={max(series):.6f}")

    candidate_summaries = build_candidate_value_summaries(rows, inspect_specs) if inspect_specs else []
    heading_summaries = build_heading_candidate_summaries(rows, inspect_specs) if inspect_specs else []
    if candidate_summaries:
        print("candidate summaries:")
        for row in candidate_summaries:
            print(
                "  - {label} {offset}:{value_format} samples={sample_count} first={first:.6f} "
                "last={last:.6f} span={span:.6f} mean_abs_step={mean_abs_step:.6f}".format(
                    **row,
                )
            )
    if heading_summaries:
        print("heading candidate summaries:")
        for row in heading_summaries:
            print(
                "  - {label} {offset}:{value_format} moving={moving_sample_count} span={span:.6f} "
                "corr_yaw={corr_with_pose_yaw:.6f}".format(
                    **row,
                )
            )

    if args.summary_json:
        payload = {
            "scenario_summaries": scenario_summaries,
            "candidate_summaries": candidate_summaries,
            "heading_candidate_summaries": heading_summaries,
        }
        path = Path(args.summary_json)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"wrote summary json: {path}")
    if args.scenario_summary_csv:
        _write_csv(Path(args.scenario_summary_csv), scenario_summaries)
        print(f"wrote scenario summary csv: {args.scenario_summary_csv}")
    if args.candidate_summary_csv:
        _write_csv(Path(args.candidate_summary_csv), candidate_summaries)
        print(f"wrote candidate summary csv: {args.candidate_summary_csv}")
    if args.heading_summary_csv:
        _write_csv(Path(args.heading_summary_csv), heading_summaries)
        print(f"wrote heading summary csv: {args.heading_summary_csv}")


def _load_capture_rows(inputs: list[str]) -> list[dict]:
    rows: list[dict] = []
    for value in inputs:
        path = Path(value)
        if path.is_dir():
            for item in sorted(path.glob("*.jsonl")):
                rows.extend(_load_capture_rows_from_file(item))
            continue
        rows.extend(_load_capture_rows_from_file(path))
    return rows


def _load_capture_rows_from_file(path: Path) -> list[dict]:
    out: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        payload = json.loads(line)
        if payload.get("type") != "sample":
            continue
        state = payload.get("state") or {}
        out.append(
            {
                "label": payload.get("label", ""),
                "sample_index": int(payload.get("sample_index", 0)),
                "mono_time_s": float(payload["frame"]["mono_time_s"]),
                "speed_mps": float(payload["frame"].get("speed_mps", 0.0) or 0.0),
                "pose_world_x": float(payload["frame"]["pose"].get("world_x", 0.0) or 0.0),
                "pose_world_z": float(payload["frame"]["pose"].get("world_z", 0.0) or 0.0),
                "pose_yaw_rad": float(payload["frame"]["pose"].get("yaw_rad", 0.0) or 0.0),
                "raw": base64.b64decode(payload["raw_b64"]),
                "velocity_x_mps": float(state.get("velocity_x_mps", 0.0)),
                "velocity_z_mps": float(state.get("velocity_z_mps", 0.0)),
                "heading_source": str(state.get("heading_source", "unknown") or "unknown"),
                "anchor_heading_locked": bool(state.get("anchor_heading_locked", False)),
                "discontinuity_detected": bool(state.get("discontinuity_detected", False)),
                "discontinuity_distance_m": (
                    float(state["discontinuity_distance_m"])
                    if state.get("discontinuity_distance_m") is not None
                    else None
                ),
            }
        )
    return out


def _read_value(raw: bytes, offset: int, value_format: str) -> float:
    if value_format == "f64":
        return float(struct.unpack_from("<d", raw, offset)[0])
    if value_format == "f32":
        return float(struct.unpack_from("<f", raw, offset)[0])
    raise ValueError(f"unsupported format: {value_format}")


def _write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
