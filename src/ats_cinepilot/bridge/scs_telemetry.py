from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, Optional

import requests

from ats_cinepilot.domain.types import Pose2D, TelemetryFrame


def _lookup_dotted(data: dict[str, Any], dotted: str, default: Any = None) -> Any:
    node: Any = data
    for part in dotted.split("."):
        if isinstance(node, dict) and part in node:
            node = node[part]
        else:
            return default
    return node


@dataclass
class JsonTelemetryConfig:
    endpoint: str
    timeout_s: float
    field_map: dict[str, str]


class HttpJsonTelemetrySource:
    """
    Generic JSON telemetry source.

    이 클래스는 특정 플러그인 스키마를 하드코딩하지 않는다.
    config의 dotted-path mapping을 통해 필수 필드를 끌어오는 방식이다.
    """

    def __init__(self, config: JsonTelemetryConfig) -> None:
        self.config = config
        self.session = requests.Session()
        self._healthy = False
        self._last_tick: int = 0

    def connect(self) -> None:
        self._healthy = True

    def is_healthy(self) -> bool:
        return self._healthy

    def read(self) -> Optional[TelemetryFrame]:
        try:
            resp = self.session.get(self.config.endpoint, timeout=self.config.timeout_s)
            resp.raise_for_status()
            payload = resp.json()
            self._healthy = True
        except Exception:
            self._healthy = False
            return None

        fmap = self.config.field_map
        tick = _lookup_dotted(payload, fmap.get("game_tick", ""), self._last_tick + 1)
        self._last_tick = int(tick)

        frame = TelemetryFrame(
            mono_time_s=time.monotonic(),
            game_tick=int(tick),
            paused=bool(_lookup_dotted(payload, fmap["paused"], False)),
            speed_mps=float(_lookup_dotted(payload, fmap["speed_mps"], 0.0) or 0.0),
            speed_limit_mps=_opt_float(_lookup_dotted(payload, fmap.get("speed_limit_mps", ""))),
            nav_distance_m=_opt_float(_lookup_dotted(payload, fmap.get("nav_distance_m", ""))),
            pose=Pose2D(
                world_x=float(_lookup_dotted(payload, fmap["pose.world_x"], 0.0) or 0.0),
                world_z=float(_lookup_dotted(payload, fmap["pose.world_z"], 0.0) or 0.0),
                yaw_rad=float(_lookup_dotted(payload, fmap["pose.yaw_rad"], 0.0) or 0.0),
            ),
        )
        return frame


def _opt_float(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


class ReplayTelemetrySource:
    def __init__(self, replay_path: str | Path) -> None:
        self.replay_path = Path(replay_path)
        self._frames: list[TelemetryFrame] = []
        self._iter: Optional[Iterator[TelemetryFrame]] = None
        self._healthy = False

    def connect(self) -> None:
        self._frames = list(self._load_frames())
        self._iter = iter(self._frames)
        self._healthy = True

    def is_healthy(self) -> bool:
        return self._healthy

    def read(self) -> Optional[TelemetryFrame]:
        if self._iter is None:
            return None
        try:
            return next(self._iter)
        except StopIteration:
            return None

    def _load_frames(self) -> Iterator[TelemetryFrame]:
        with self.replay_path.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                row = json.loads(line)
                pose = row["pose"]
                yield TelemetryFrame(
                    mono_time_s=float(row["mono_time_s"]),
                    game_tick=int(row["game_tick"]),
                    paused=bool(row["paused"]),
                    speed_mps=float(row["speed_mps"]),
                    speed_limit_mps=_opt_float(row.get("speed_limit_mps")),
                    nav_distance_m=_opt_float(row.get("nav_distance_m")),
                    pose=Pose2D(
                        world_x=float(pose["world_x"]),
                        world_z=float(pose["world_z"]),
                        yaw_rad=float(pose["yaw_rad"]),
                    ),
                )


class NullTelemetrySource:
    def connect(self) -> None:
        return None

    def is_healthy(self) -> bool:
        return True

    def read(self) -> Optional[TelemetryFrame]:
        return None
