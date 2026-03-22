from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(slots=True)
class HudPreset:
    name: str
    normalized_roi: tuple[float, float, float, float]
    normalized_signature_roi: tuple[float, float, float, float]
    red_hsv_ranges: list[tuple[tuple[int, int, int], tuple[int, int, int]]]
    erode_iters: int = 1
    dilate_iters: int = 2
    blur_kernel: int = 3
    min_route_pixels: int = 120
    player_icon_mask_enabled: bool = False
    player_icon_mask_roi: tuple[float, float, float, float] | None = None


def load_preset(path: str | Path) -> HudPreset:
    payload = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    player_mask = payload.get("player_icon_mask", {})
    return HudPreset(
        name=payload["name"],
        normalized_roi=tuple(payload["normalized_roi"]),
        normalized_signature_roi=tuple(payload["normalized_signature_roi"]),
        red_hsv_ranges=[
            (tuple(low), tuple(high))
            for low, high in payload["red_hsv_ranges"]
        ],
        erode_iters=int(payload.get("erode_iters", 1)),
        dilate_iters=int(payload.get("dilate_iters", 2)),
        blur_kernel=int(payload.get("blur_kernel", 3)),
        min_route_pixels=int(payload.get("min_route_pixels", 120)),
        player_icon_mask_enabled=bool(player_mask.get("enabled", False)),
        player_icon_mask_roi=tuple(player_mask["normalized_roi"]) if player_mask.get("normalized_roi") else None,
    )


def denormalize_roi(frame_shape: tuple[int, int, int] | tuple[int, int], roi: tuple[float, float, float, float]) -> tuple[int, int, int, int]:
    height, width = frame_shape[:2]
    x, y, w, h = roi
    left = int(width * x)
    top = int(height * y)
    right = int(width * (x + w))
    bottom = int(height * (y + h))
    return left, top, right, bottom


def crop_roi(frame: Any, roi: tuple[int, int, int, int]):
    left, top, right, bottom = roi
    return frame[top:bottom, left:right]
