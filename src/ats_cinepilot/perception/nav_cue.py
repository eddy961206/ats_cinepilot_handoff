from __future__ import annotations

import numpy as np


def estimate_turn_bias(mask: np.ndarray) -> float:
    """
    -1 left ~ +1 right

    아주 단순한 기하 추정.
    아래쪽 route 중심과 위쪽 route 중심의 x 차이로 turn bias를 만든다.
    """
    if mask.size == 0:
        return 0.0

    ys, xs = np.where(mask > 0)
    if len(xs) == 0:
        return 0.0

    h, w = mask.shape[:2]
    bottom_band = mask[int(h * 0.70): int(h * 0.98), :]
    top_band = mask[int(h * 0.15): int(h * 0.45), :]

    def center_x(band: np.ndarray) -> float | None:
        yx = np.where(band > 0)
        if len(yx[1]) == 0:
            return None
        return float(np.mean(yx[1]))

    bx = center_x(bottom_band)
    tx = center_x(top_band)
    if bx is None or tx is None:
        return 0.0

    delta = (tx - bx) / max(float(w), 1.0)
    return max(-1.0, min(1.0, delta * 4.0))
