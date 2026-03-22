from __future__ import annotations

import argparse
import logging

from ats_cinepilot.app import AutopilotApp
from ats_cinepilot.ops.config import resolve_config, validate_runtime_config
from ats_cinepilot.ops.logger import setup_logging


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ats-cinepilot")
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run")
    run.add_argument("--config", action="append", required=True, help="YAML config path. Can be repeated.")
    run.add_argument("--mode", choices=["shadow", "active"], default="shadow")
    run.add_argument("--steps", type=int, default=None)

    check = sub.add_parser("check-config")
    check.add_argument("--config", action="append", required=True)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    setup_logging(logging.INFO)

    if args.command == "check-config":
        cfg = resolve_config(args.config)
        issues = validate_runtime_config(cfg)
        if issues:
            print("config validation FAILED")
            for issue in issues:
                print(f"- {issue}")
            raise SystemExit(1)
        print("config loaded OK")
        print("config validation OK")
        print(cfg)
        return

    if args.command == "run":
        cfg = resolve_config(args.config)
        issues = validate_runtime_config(cfg, mode=args.mode)
        if issues:
            print("config validation FAILED")
            for issue in issues:
                print(f"- {issue}")
            raise SystemExit(1)
        app = AutopilotApp(cfg, mode=args.mode)
        app.run_loop(steps=args.steps)
        return


if __name__ == "__main__":
    main()
