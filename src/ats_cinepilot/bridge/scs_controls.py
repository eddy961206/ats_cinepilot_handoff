from __future__ import annotations

import importlib
import json
import sys
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ats_cinepilot.domain.types import VehicleCommand


@dataclass
class ModuleControlConfig:
    module_name: str
    class_name: str
    apply_method: str = ""
    neutral_method: str = ""
    field_mapping: dict[str, str] | None = None
    module_search_paths: list[str] | None = None


def resolve_module_search_paths(paths: list[str] | None) -> list[str]:
    if not paths:
        return []
    resolved: list[str] = []
    for raw_path in paths:
        path = Path(raw_path).expanduser().resolve()
        if path.exists():
            resolved.append(str(path))
    return resolved


@contextmanager
def control_module_import_scope(paths: list[str] | None):
    inserted: list[str] = []
    for resolved in reversed(resolve_module_search_paths(paths)):
        if resolved in sys.path:
            continue
        sys.path.insert(0, resolved)
        inserted.append(resolved)
    try:
        yield
    finally:
        for resolved in inserted:
            if resolved in sys.path:
                sys.path.remove(resolved)


def load_control_class(config: ModuleControlConfig):
    with control_module_import_scope(config.module_search_paths):
        module = importlib.import_module(config.module_name)
        return getattr(module, config.class_name)


class DynamicModuleControlSink:
    """
    Generic control sink.

    실제 `scs-sdk-controller` 연동은 로컬 codex가 이 래퍼를 기준으로
    attribute/method 이름을 맞추면 된다.
    """

    def __init__(self, config: ModuleControlConfig) -> None:
        self.config = config
        self._healthy = False
        self._obj: Any = None

    def connect(self) -> None:
        klass = load_control_class(self.config)
        self._obj = klass()
        self._healthy = True

    def is_healthy(self) -> bool:
        return self._healthy

    def apply(self, command: VehicleCommand) -> None:
        if self._obj is None:
            raise RuntimeError("control sink not connected")
        cmd = command.clipped()
        if self.config.apply_method:
            getattr(self._obj, self.config.apply_method)(cmd)
            return

        mapping = self.config.field_mapping or {}
        payload = {
            mapping.get("steering", "steering"): cmd.steering,
            mapping.get("throttle", "throttle"): cmd.throttle,
            mapping.get("brake", "brake"): cmd.brake,
            mapping.get("left_blinker", "left_blinker"): cmd.left_blinker,
            mapping.get("right_blinker", "right_blinker"): cmd.right_blinker,
        }
        for key, value in payload.items():
            if hasattr(self._obj, key):
                setattr(self._obj, key, value)

    def neutralize(self) -> None:
        if self._obj is None:
            return
        if self.config.neutral_method:
            getattr(self._obj, self.config.neutral_method)()
            return
        self.apply(VehicleCommand(0.0, 0.0, 0.0))


class NoopControlSink:
    def connect(self) -> None:
        return None

    def is_healthy(self) -> bool:
        return True

    def apply(self, command: VehicleCommand) -> None:
        _ = command

    def neutralize(self) -> None:
        return None


class RecordingControlSink:
    def __init__(self, output_path: str | Path) -> None:
        self.output_path = Path(output_path)
        self._healthy = False

    def connect(self) -> None:
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self._healthy = True

    def is_healthy(self) -> bool:
        return self._healthy

    def apply(self, command: VehicleCommand) -> None:
        with self.output_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(command.__dict__, ensure_ascii=False) + "\n")

    def neutralize(self) -> None:
        self.apply(VehicleCommand(0.0, 0.0, 0.0))
