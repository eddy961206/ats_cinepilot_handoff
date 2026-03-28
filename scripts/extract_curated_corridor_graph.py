from __future__ import annotations

import argparse
from pathlib import Path

from ats_cinepilot.map.cache import load_graph_cache, save_graph_cache
from ats_cinepilot.map.curated_corridor import extract_curated_corridor_graph, normalize_cache_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="source graph cache path")
    parser.add_argument("--output", required=True, help="output curated graph cache path")
    parser.add_argument("--corridor-name", required=True)
    parser.add_argument("--graph-source", required=True)
    parser.add_argument("--alignment-mode", required=True)
    parser.add_argument("--edge", action="append", dest="edges", required=True)
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    graph = load_graph_cache(input_path)
    curated = extract_curated_corridor_graph(
        graph,
        corridor_name=args.corridor_name,
        edge_sequence=args.edges,
        graph_source=args.graph_source,
        alignment_mode=args.alignment_mode,
        source_cache_path=normalize_cache_path(input_path),
    )
    save_graph_cache(curated, output_path)
    print(f"saved curated corridor graph: {output_path}")
    print(f"  graph_source={curated.metadata.get('graph_source')}")
    print(f"  corridor_name={curated.metadata.get('corridor_name')}")
    print(f"  approved_edge_sequence={curated.metadata.get('approved_edge_sequence')}")


if __name__ == "__main__":
    main()
