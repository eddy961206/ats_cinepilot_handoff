from __future__ import annotations

import argparse
from pathlib import Path

from ats_cinepilot.ops.control_plugin_patch import patch_scs_sdk_controller_file


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, help="Path to external scs-sdk-controller repo")
    args = parser.parse_args()

    repo_path = Path(args.repo)
    target = repo_path / "scs_sdk_controller.cpp"
    changed = patch_scs_sdk_controller_file(target)
    if changed:
        print(f"patched control plugin source: {target}")
    else:
        print(f"control plugin source already patched: {target}")


if __name__ == "__main__":
    main()
