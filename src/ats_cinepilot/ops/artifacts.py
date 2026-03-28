from __future__ import annotations

from pathlib import Path
from typing import Any

import cv2

from ats_cinepilot.ops.recorder import JsonlRecorder


class CvArtifactWriter:
    def __init__(
        self,
        *,
        artifact_dir: str,
        save_video: bool,
        save_frames: bool,
        summary_jsonl_path: str | None,
    ) -> None:
        self.artifact_dir = Path(artifact_dir)
        self.save_video = save_video
        self.save_frames = save_frames
        self.summary_recorder = JsonlRecorder(summary_jsonl_path) if summary_jsonl_path else None
        self._video_writer = None
        self._video_path = self.artifact_dir / "observer_overlay.mp4"

    @property
    def video_path(self) -> Path:
        return self._video_path

    def write(
        self,
        *,
        frame_index: int,
        overlay_bgr,
        summary: dict[str, Any],
    ) -> str | None:
        self.artifact_dir.mkdir(parents=True, exist_ok=True)
        if self.save_frames:
            frame_path = self.artifact_dir / f"frame_{frame_index:05d}.jpg"
            cv2.imwrite(str(frame_path), overlay_bgr)
            summary["overlay_path"] = str(frame_path)
        if self.save_video:
            self._ensure_video_writer(overlay_bgr.shape[1], overlay_bgr.shape[0])
            self._video_writer.write(overlay_bgr)
        if self.summary_recorder is not None:
            self.summary_recorder.write(summary)
        return summary.get("overlay_path")

    def close(self) -> None:
        if self._video_writer is not None:
            self._video_writer.release()
            self._video_writer = None

    def _ensure_video_writer(self, width: int, height: int) -> None:
        if self._video_writer is not None:
            return
        self.artifact_dir.mkdir(parents=True, exist_ok=True)
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        self._video_writer = cv2.VideoWriter(str(self._video_path), fourcc, 12.0, (width, height))
