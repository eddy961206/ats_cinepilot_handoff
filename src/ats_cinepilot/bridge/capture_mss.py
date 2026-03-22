from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class MSSConfig:
    region: tuple[int, int, int, int]


class MSSCaptureSource:
    def __init__(self, config: MSSConfig) -> None:
        self.config = config
        self._mss = None

    def start(self) -> None:
        try:
            from mss import mss
        except ImportError as exc:
            raise RuntimeError(
                "mss is not installed. Install dependency: pip install mss"
            ) from exc
        self._mss = mss()

    def grab(self):
        if self._mss is None:
            raise RuntimeError("MSSCaptureSource not started")
        left, top, right, bottom = self.config.region
        shot = self._mss.grab({
            "left": left,
            "top": top,
            "width": right - left,
            "height": bottom - top,
        })
        return np.array(shot)

    def stop(self) -> None:
        self._mss = None
