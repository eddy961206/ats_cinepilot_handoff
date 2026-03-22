from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class JsonlRecorder:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def write(self, row: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
