from __future__ import annotations

from typing import Any

import cv2
import numpy as np

from .hud_layout import HudPreset


def extract_route_mask(roi_bgr: Any, preset: HudPreset) -> np.ndarray:
    img = np.asarray(roi_bgr)
    if img.shape[-1] == 4:
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

    if preset.blur_kernel > 1:
        k = preset.blur_kernel if preset.blur_kernel % 2 == 1 else preset.blur_kernel + 1
        img = cv2.GaussianBlur(img, (k, k), 0)

    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    mask = np.zeros(hsv.shape[:2], dtype=np.uint8)
    for low, high in preset.red_hsv_ranges:
        local = cv2.inRange(hsv, np.array(low, dtype=np.uint8), np.array(high, dtype=np.uint8))
        mask = cv2.bitwise_or(mask, local)

    if preset.player_icon_mask_enabled and preset.player_icon_mask_roi:
        h, w = mask.shape[:2]
        x, y, rw, rh = preset.player_icon_mask_roi
        left = int(w * x)
        top = int(h * y)
        right = int(w * (x + rw))
        bottom = int(h * (y + rh))
        mask[top:bottom, left:right] = 0

    kernel = np.ones((3, 3), np.uint8)
    if preset.erode_iters > 0:
        mask = cv2.erode(mask, kernel, iterations=preset.erode_iters)
    if preset.dilate_iters > 0:
        mask = cv2.dilate(mask, kernel, iterations=preset.dilate_iters)

    return mask


def route_pixel_count(mask: np.ndarray) -> int:
    return int((mask > 0).sum())
