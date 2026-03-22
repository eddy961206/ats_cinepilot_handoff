from __future__ import annotations

import argparse

from ats_cinepilot.app import AutopilotApp
from ats_cinepilot.ops.config import resolve_config


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", action="append", required=True)
    parser.add_argument("--steps", type=int, default=100)
    args = parser.parse_args()

    cfg = resolve_config(args.config)
    app = AutopilotApp(cfg, mode="shadow")
    app.run_loop(steps=args.steps)
    print("replay session completed")


if __name__ == "__main__":
    main()
