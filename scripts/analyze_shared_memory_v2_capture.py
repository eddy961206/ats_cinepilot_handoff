from __future__ import annotations

import argparse
import base64
import json
import struct
from pathlib import Path

from ats_cinepilot.bridge.shared_memory_v2_analysis import rank_axis_candidates


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", action="append", required=True, help="Capture jsonl file or directory. Can repeat.")
    parser.add_argument("--top", type=int, default=8)
    parser.add_argument("--inspect", action="append", default=[], help="Offset spec like 285:f64")
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

    for spec in args.inspect:
        offset_str, value_format = spec.split(":", maxsplit=1)
        offset = int(offset_str)
        series = [_read_value(row["raw"], offset, value_format) for row in rows]
        print(f"inspect {spec}: first={series[0]:.6f} last={series[-1]:.6f} min={min(series):.6f} max={max(series):.6f}")


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
                "mono_time_s": float(payload["frame"]["mono_time_s"]),
                "raw": base64.b64decode(payload["raw_b64"]),
                "velocity_x_mps": float(state.get("velocity_x_mps", 0.0)),
                "velocity_z_mps": float(state.get("velocity_z_mps", 0.0)),
            }
        )
    return out


def _read_value(raw: bytes, offset: int, value_format: str) -> float:
    if value_format == "f64":
        return float(struct.unpack_from("<d", raw, offset)[0])
    if value_format == "f32":
        return float(struct.unpack_from("<f", raw, offset)[0])
    raise ValueError(f"unsupported format: {value_format}")


if __name__ == "__main__":
    main()
