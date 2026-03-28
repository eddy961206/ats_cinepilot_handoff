from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = REPO_ROOT / "state" / "latest_session_state.json"
BRIEF_PATH = REPO_ROOT / "docs" / "ops" / "NEXT_AGENT_BRIEF.md"
AUTO_BEGIN = "<!-- BEGIN AUTO-GENERATED FACTS -->"
AUTO_END = "<!-- END AUTO-GENERATED FACTS -->"


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=REPO_ROOT, text=True).strip()


def merge_auto_generated_section(existing: str, generated: str) -> str:
    if AUTO_BEGIN in existing and AUTO_END in existing:
        start = existing.index(AUTO_BEGIN)
        end = existing.index(AUTO_END) + len(AUTO_END)
        merged = existing[:start] + generated + existing[end:]
    else:
        merged = existing.rstrip() + "\n\n" + generated + "\n"
    return merged if merged.endswith("\n") else merged + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--focus", default="cv_observer_overlay_and_handoff_harness")
    parser.add_argument("--stage", default="C3.5")
    parser.add_argument("--command", action="append", default=[])
    parser.add_argument("--config", action="append", default=[])
    parser.add_argument("--artifact", action="append", default=[])
    parser.add_argument("--blocker", action="append", default=[])
    args = parser.parse_args()

    branch = _git("branch", "--show-current")
    commit = _git("rev-parse", "HEAD")
    now = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")

    state = {
        "timestamp": now,
        "base_branch": "main",
        "base_commit": _git("merge-base", "HEAD", "main"),
        "working_branch": branch,
        "current_stage": args.stage,
        "current_focus": args.focus,
        "last_known_good_commands": args.command,
        "active_configs": args.config,
        "latest_artifacts": args.artifact,
        "open_blockers": args.blocker,
        "head_commit": commit,
    }
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")

    generated = "\n".join(
        [
            AUTO_BEGIN,
            f"- auto base: `main@{state['base_commit']}`",
            f"- auto branch: `{branch}`",
            f"- auto stage: `{args.stage}`",
            f"- auto focus: `{args.focus}`",
            f"- auto head commit: `{commit}`",
            "- auto last known good commands:",
            *[f"  - `{item}`" for item in args.command],
            "- auto latest artifacts:",
            *[f"  - `{item}`" for item in args.artifact],
            "- auto blockers:",
            *[f"  - `{item}`" for item in args.blocker],
            AUTO_END,
        ]
    )
    BRIEF_PATH.parent.mkdir(parents=True, exist_ok=True)
    existing = BRIEF_PATH.read_text(encoding="utf-8") if BRIEF_PATH.exists() else f"{AUTO_BEGIN}\n{AUTO_END}\n"
    brief = merge_auto_generated_section(existing, generated)
    BRIEF_PATH.write_text(brief, encoding="utf-8")

    print(f"updated {STATE_PATH}")
    print(f"updated {BRIEF_PATH}")


if __name__ == "__main__":
    main()
