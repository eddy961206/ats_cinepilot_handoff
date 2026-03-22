from __future__ import annotations

import argparse

from ats_cinepilot.map.adapters.trucksim_maps import load_trucksim_graph
from ats_cinepilot.map.adapters.ts_map import load_ts_map_graph
from ats_cinepilot.map.cache import save_graph_cache


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", choices=["trucksim", "ts-map"], required=True)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    if args.source == "trucksim":
        graph = load_trucksim_graph(args.input)
    else:
        graph = load_ts_map_graph(args.input)

    save_graph_cache(graph, args.output)
    print(f"saved internal graph cache to {args.output}")


if __name__ == "__main__":
    main()
