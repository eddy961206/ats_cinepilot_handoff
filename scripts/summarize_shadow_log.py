from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", action="append", required=True, help="jsonl log file. Can repeat.")
    parser.add_argument("--json", default="")
    args = parser.parse_args()

    summaries = [summarize_log(Path(path)) for path in args.input]
    for summary in summaries:
        print_summary(summary)

    if args.json:
        output_path = Path(args.json)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(summaries, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"saved summary json: {output_path}")


def summarize_log(path: Path) -> dict:
    safety_counts: Counter[str] = Counter()
    heading_counts: Counter[str] = Counter()
    graph_failure_counts: Counter[str] = Counter()
    selected_reason_counts: Counter[str] = Counter()
    direction_confidence_counts: Counter[str] = Counter()
    demo_guard_reason_counts: Counter[str] = Counter()
    match_values: list[float] = []
    route_values: list[float] = []
    cte_values: list[float] = []
    near_values: list[float] = []
    candidate_values: list[int] = []
    steering_abs_values: list[float] = []
    non_trivial_steering_count = 0
    throttle_command_count = 0
    brake_command_count = 0
    first_match_lost_step: int | None = None
    first_route_confidence_low_step: int | None = None
    last_status: dict = {}
    total_steps = 0

    with path.open("r", encoding="utf-8") as handle:
        for index, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            total_steps += 1
            status = dict(row.get("status", {}))
            last_status = status or last_status
            safety = str(status.get("safety_decision", "UNKNOWN"))
            safety_counts[safety] += 1
            heading_counts[str(status.get("heading_source", "unknown"))] += 1
            graph_failure_counts[str(status.get("graph_failure", "None"))] += 1
            if status.get("selected_reason") is not None:
                selected_reason_counts[str(status["selected_reason"])] += 1
            if status.get("direction_confidence_state") is not None:
                direction_confidence_counts[str(status["direction_confidence_state"])] += 1
            if status.get("demo_guard_reason") is not None:
                demo_guard_reason_counts[str(status["demo_guard_reason"])] += 1
            if safety == "MATCH_LOST" and first_match_lost_step is None:
                first_match_lost_step = index
            if safety == "ROUTE_CONFIDENCE_LOW" and first_route_confidence_low_step is None:
                first_route_confidence_low_step = index

            _append_numeric(match_values, status.get("map_match_confidence"))
            _append_numeric(route_values, status.get("route_confidence"))
            _append_numeric(cte_values, status.get("cross_track_error_m"))
            _append_numeric(near_values, status.get("nearest_edge_distance_m"))
            if status.get("graph_candidate_count") is not None:
                candidate_values.append(int(status["graph_candidate_count"]))
            command = dict(row.get("command", {}))
            steering = _coerce_float(command.get("steering"))
            throttle = _coerce_float(command.get("throttle"))
            brake = _coerce_float(command.get("brake"))
            if steering is not None:
                steering_abs_values.append(abs(steering))
                if abs(steering) >= 0.05:
                    non_trivial_steering_count += 1
            if throttle is not None and throttle > 0.0:
                throttle_command_count += 1
            if brake is not None and brake > 0.0:
                brake_command_count += 1

    return {
        "path": str(path),
        "steps": total_steps,
        "graph_source": last_status.get("graph_source"),
        "alignment_mode": last_status.get("alignment_mode"),
        "pose_source": last_status.get("pose_source"),
        "pose_frame": last_status.get("pose_frame"),
        "safety_counts": dict(safety_counts),
        "heading_source_counts": dict(heading_counts),
        "graph_failure_counts": dict(graph_failure_counts),
        "selected_reason_counts": dict(selected_reason_counts),
        "direction_confidence_state_counts": dict(direction_confidence_counts),
        "demo_guard_reason_counts": dict(demo_guard_reason_counts),
        "first_match_lost_step": first_match_lost_step,
        "first_route_confidence_low_step": first_route_confidence_low_step,
        "match_confidence_min": min(match_values) if match_values else None,
        "match_confidence_max": max(match_values) if match_values else None,
        "route_confidence_min": min(route_values) if route_values else None,
        "route_confidence_max": max(route_values) if route_values else None,
        "cross_track_error_max": max(cte_values) if cte_values else None,
        "nearest_edge_distance_min": min(near_values) if near_values else None,
        "nearest_edge_distance_max": max(near_values) if near_values else None,
        "graph_candidate_count_min": min(candidate_values) if candidate_values else None,
        "graph_candidate_count_max": max(candidate_values) if candidate_values else None,
        "steering_abs_max": max(steering_abs_values) if steering_abs_values else None,
        "non_trivial_steering_count": non_trivial_steering_count,
        "throttle_command_count": throttle_command_count,
        "brake_command_count": brake_command_count,
    }


def print_summary(summary: dict) -> None:
    print(f"log: {summary['path']}")
    print(
        "  graph={graph}/{align} pose={pose_source}/{pose_frame} steps={steps}".format(
            graph=summary.get("graph_source"),
            align=summary.get("alignment_mode"),
            pose_source=summary.get("pose_source"),
            pose_frame=summary.get("pose_frame"),
            steps=summary["steps"],
        )
    )
    print(
        "  safety={safety} first_MATCH_LOST={first_match_lost} first_ROUTE_CONFIDENCE_LOW={first_route_low} "
        "match=[{match_min}, {match_max}] route=[{route_min}, {route_max}] "
        "cte_max={cte_max} near=[{near_min}, {near_max}] cand=[{cand_min}, {cand_max}]".format(
            safety=summary["safety_counts"],
            first_match_lost=summary["first_match_lost_step"],
            first_route_low=summary["first_route_confidence_low_step"],
            match_min=_fmt(summary["match_confidence_min"]),
            match_max=_fmt(summary["match_confidence_max"]),
            route_min=_fmt(summary["route_confidence_min"]),
            route_max=_fmt(summary["route_confidence_max"]),
            cte_max=_fmt(summary["cross_track_error_max"]),
            near_min=_fmt(summary["nearest_edge_distance_min"]),
            near_max=_fmt(summary["nearest_edge_distance_max"]),
            cand_min=summary["graph_candidate_count_min"],
            cand_max=summary["graph_candidate_count_max"],
        )
    )
    print(f"  heading_sources={summary['heading_source_counts']}")
    print(f"  graph_failures={summary['graph_failure_counts']}")
    print(f"  selected_reasons={summary['selected_reason_counts']}")
    print(f"  direction_confidence={summary['direction_confidence_state_counts']}")
    print(
        "  steering_abs_max={steering_max} non_trivial_steering_count={steering_count} "
        "throttle_command_count={throttle_count} brake_command_count={brake_count}".format(
            steering_max=_fmt(summary.get("steering_abs_max")),
            steering_count=summary.get("non_trivial_steering_count", 0),
            throttle_count=summary.get("throttle_command_count", 0),
            brake_count=summary.get("brake_command_count", 0),
        )
    )
    print(f"  demo_guard_reasons={summary['demo_guard_reason_counts']}")


def _append_numeric(values: list[float], value: object) -> None:
    if value is None:
        return
    values.append(float(value))


def _coerce_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _fmt(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.3f}"


if __name__ == "__main__":
    main()
