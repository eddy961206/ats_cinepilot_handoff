from __future__ import annotations

import argparse
from pathlib import Path

from ats_cinepilot.map.cache import save_graph_cache
from ats_cinepilot.ops.demo_corridor import build_curated_corridor_graph, load_demo_corridor_contract

DEFAULT_CONTRACT_PATH = Path("configs/corridors/demo_dense_curated_corridor.yaml")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", default=str(DEFAULT_CONTRACT_PATH))
    parser.add_argument("--output", default="")
    args = parser.parse_args()

    contract = load_demo_corridor_contract(args.contract)
    graph = build_curated_corridor_graph(contract)
    output_path = Path(args.output) if args.output else Path(contract.graph_cache_path)
    save_graph_cache(graph, output_path)
    print(f"saved curated corridor graph: {output_path}")
    print(f"graph_source={graph.metadata.get('graph_source')}")
    print(f"alignment_mode={graph.metadata.get('alignment_mode')}")
    print(f"edge_count={len(graph.edges)} node_count={len(graph.nodes)}")


if __name__ == "__main__":
    main()
