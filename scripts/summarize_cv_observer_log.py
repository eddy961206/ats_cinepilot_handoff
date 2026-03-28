from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    args = parser.parse_args()

    path = Path(args.input)
    rows = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if not rows:
        print("cv_summary=empty")
        return

    lane_confidences = [float(row.get("lane_confidence", 0.0)) for row in rows]
    lead_confidences = [
        float(row.get("lead_vehicle_confidence", 0.0))
        for row in rows
        if row.get("lead_vehicle_detected", False)
    ]
    overlay_paths = [row.get("overlay_path") for row in rows if row.get("overlay_path")]
    cv_guard_reasons: dict[str, int] = {}
    lane_detected_count = 0
    lead_detected_count = 0
    for row in rows:
        if row.get("lane_detected", False):
            lane_detected_count += 1
        if row.get("lead_vehicle_detected", False):
            lead_detected_count += 1
        reason = str(row.get("cv_guard_reason") or "none")
        cv_guard_reasons[reason] = cv_guard_reasons.get(reason, 0) + 1

    print(
        "frames={frames} lane_detected={lane_detected} lead_detected={lead_detected} "
        "lane_conf=[{lane_min:.3f}, {lane_max:.3f}] "
        "lead_conf=[{lead_min:.3f}, {lead_max:.3f}] "
        "guard_reasons={guard_reasons} overlay_samples={overlays}".format(
            frames=len(rows),
            lane_detected=lane_detected_count,
            lead_detected=lead_detected_count,
            lane_min=min(lane_confidences),
            lane_max=max(lane_confidences),
            lead_min=min(lead_confidences) if lead_confidences else 0.0,
            lead_max=max(lead_confidences) if lead_confidences else 0.0,
            guard_reasons=cv_guard_reasons,
            overlays=min(3, len(overlay_paths)),
        )
    )
    if overlay_paths:
        for overlay_path in overlay_paths[:3]:
            print(f"overlay_sample={overlay_path}")


if __name__ == "__main__":
    main()
