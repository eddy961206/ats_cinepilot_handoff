from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DXcamConfig:
    monitor_index: int
    region: tuple[int, int, int, int]
    target_fps: int = 12


class DXcamCaptureSource:
    def __init__(self, config: DXcamConfig) -> None:
        self.config = config
        self._camera = None

    def start(self) -> None:
        try:
            import dxcam  # type: ignore
        except ImportError as exc:
            raise RuntimeError(
                "DXcam is not installed. Install optional dependency: pip install -e '.[windows]'"
            ) from exc
        self._camera = dxcam.create(output_idx=self.config.monitor_index)
        self._camera.start(region=self.config.region, target_fps=self.config.target_fps)

    def grab(self):
        if self._camera is None:
            raise RuntimeError("DXcamCaptureSource not started")
        return self._camera.get_latest_frame()

    def stop(self) -> None:
        if self._camera is not None:
            self._camera.stop()
