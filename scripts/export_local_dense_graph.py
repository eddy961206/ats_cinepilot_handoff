from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from ats_cinepilot.map.adapters.trucksim_maps import crop_graph_to_radius, load_trucksim_graph
from ats_cinepilot.map.cache import save_graph_cache

try:
    from scripts.export_map import read_center_from_config
except ModuleNotFoundError:  # pragma: no cover - direct script execution fallback
    from export_map import read_center_from_config


REQUIRED_PARSER_FILES = (
    "usa-nodes.json",
    "usa-roads.json",
    "usa-prefabs.json",
    "usa-prefabDescriptions.json",
    "usa-roadLooks.json",
)
DEFAULT_PARSER_OUTPUT_DIR = "data/maps/trucksim_parser/ats_local"
DEFAULT_GEOJSON_OUTPUT_DIR = "data/maps/trucksim_geojson/ats_local_region"
DEFAULT_OUTPUT_CACHE = "data/maps/cache/ats_usa_region_dense_local_geojson_8km.json"
DEFAULT_RADIUS_M = 8000.0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", action="append", required=True, help="Config path(s) used to read the live crop center.")
    parser.add_argument("--game-dir", default="", help="ATS installation dir containing .scs files.")
    parser.add_argument("--toolchain-dir", default="", help="Path to local trucksim_maps_repo checkout.")
    parser.add_argument("--parser-output-dir", default=DEFAULT_PARSER_OUTPUT_DIR)
    parser.add_argument("--geojson-output-dir", default=DEFAULT_GEOJSON_OUTPUT_DIR)
    parser.add_argument("--output-cache", default=DEFAULT_OUTPUT_CACHE)
    parser.add_argument("--radius-m", type=float, default=DEFAULT_RADIUS_M)
    parser.add_argument(
        "--synthetic-reverse-edges",
        action="store_true",
        help="Add reverse edges for each ATS road feature. Keep disabled for primary direction-semantics validation.",
    )
    parser.add_argument("--force-parse", action="store_true")
    args = parser.parse_args()

    game_dir = _resolve_game_dir(args.game_dir)
    toolchain_dir = _resolve_toolchain_dir(args.toolchain_dir)
    parser_output_dir = Path(args.parser_output_dir).resolve()
    geojson_output_dir = Path(args.geojson_output_dir).resolve()
    output_cache = Path(args.output_cache).resolve()
    center_x_m, center_z_m = read_center_from_config(args.config)

    _ensure_toolchain_ready(toolchain_dir)
    if args.force_parse or not _has_parser_output(parser_output_dir):
        _run(
            [
                "npx",
                "tsx",
                "packages/clis/parser/index.ts",
                "-i",
                str(game_dir),
                "-o",
                str(parser_output_dir),
            ],
            cwd=toolchain_dir,
        )
    else:
        print(f"reusing parser output at {parser_output_dir}")

    geojson_output_dir.mkdir(parents=True, exist_ok=True)
    _run(
        [
            "npx",
            "tsx",
            "packages/clis/generator/index.ts",
            "map",
            "-m",
            "usa",
            "-i",
            str(parser_output_dir),
            "-o",
            str(geojson_output_dir),
            "-t",
            "geojson",
            "--focusGameCoords",
            f"{center_x_m},{center_z_m}",
            "--focusRadius",
            str(int(args.radius_m)),
            "--skipCoalescing",
        ],
        cwd=toolchain_dir,
    )

    geojson_path = geojson_output_dir / "ats.geojson"
    if not geojson_path.exists():
        raise FileNotFoundError(f"generator did not create {geojson_path}")

    graph = load_trucksim_graph(geojson_path, add_synthetic_reverse_edges=args.synthetic_reverse_edges)
    graph = crop_graph_to_radius(
        graph,
        center_x_m=float(center_x_m),
        center_z_m=float(center_z_m),
        radius_m=float(args.radius_m),
    )
    graph.metadata.update(
        {
            "graph_source": "trucksim_local_geojson_region",
            "alignment_mode": "ats_absolute_identity",
            "export_toolchain": "trucksim_maps_parser_map_geojson_skip_coalescing",
            "exported_at_utc": datetime.now(timezone.utc).isoformat(),
            "focus_center_x_m": float(center_x_m),
            "focus_center_z_m": float(center_z_m),
            "focus_radius_m": float(args.radius_m),
            "synthetic_reverse_edges": bool(args.synthetic_reverse_edges),
            "source_game_dir": str(game_dir),
            "source_parser_dir": str(parser_output_dir),
            "source_input": str(geojson_path),
        }
    )
    save_graph_cache(graph, output_cache, indent=2)
    print(
        json.dumps(
            {
                "output_cache": str(output_cache),
                "node_count": len(graph.nodes),
                "edge_count": len(graph.edges),
                "graph_source": graph.metadata["graph_source"],
                "alignment_mode": graph.metadata["alignment_mode"],
                "focus_center_x_m": graph.metadata["focus_center_x_m"],
                "focus_center_z_m": graph.metadata["focus_center_z_m"],
                "focus_radius_m": graph.metadata["focus_radius_m"],
            },
            ensure_ascii=False,
        )
    )


def _resolve_game_dir(raw: str) -> Path:
    candidates = [Path(raw)] if raw else [
        Path(r"D:\Steam\steamapps\common\American Truck Simulator"),
        Path(r"C:\Program Files (x86)\Steam\steamapps\common\American Truck Simulator"),
    ]
    for candidate in candidates:
        if candidate.exists() and any(candidate.glob("*.scs")):
            return candidate
    raise FileNotFoundError("ATS game dir not found. Pass --game-dir explicitly.")


def _resolve_toolchain_dir(raw: str) -> Path:
    candidates = [Path(raw)] if raw else [
        Path(__file__).resolve().parents[2] / "_ext" / "trucksim_maps_repo",
        Path(r"C:\workspaces\python_workspace\_ext\trucksim_maps_repo"),
    ]
    for candidate in candidates:
        if (candidate / "packages" / "clis" / "parser" / "index.ts").exists():
            return candidate
    raise FileNotFoundError("trucksim_maps_repo not found. Pass --toolchain-dir explicitly.")


def _has_parser_output(path: Path) -> bool:
    return all((path / name).exists() for name in REQUIRED_PARSER_FILES)


def _ensure_toolchain_ready(toolchain_dir: Path) -> None:
    if not (toolchain_dir / "node_modules" / "tsx" / "dist" / "cli.mjs").exists():
        raise FileNotFoundError(
            f"toolchain dependencies missing under {toolchain_dir}. Run `npm install --ignore-scripts` there first."
        )
    if not (toolchain_dir / "packages" / "clis" / "parser" / "build" / "Release" / "gdeflate.node").exists():
        raise FileNotFoundError(
            f"parser native build missing under {toolchain_dir}. Run `npm install` or `node-gyp rebuild` in packages/clis/parser first."
        )


def _run(command: list[str], *, cwd: Path) -> None:
    executable = shutil.which(command[0]) or shutil.which(f"{command[0]}.cmd")
    if executable is None:
        raise FileNotFoundError(f"executable not found: {command[0]}")
    resolved_command = [executable, *command[1:]]
    print(f"running: {' '.join(command)}")
    subprocess.run(resolved_command, cwd=cwd, check=True)


if __name__ == "__main__":
    main()
