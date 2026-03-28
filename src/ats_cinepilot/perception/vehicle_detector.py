from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
import requests

from ats_cinepilot.perception.observer_types import LeadVehicleObservation, VehicleDetection


TF_SSD_V3_MODEL_URL = (
    "https://raw.githubusercontent.com/KelvinPuyam/Real-time-object-detection/main/"
    "frozen_inference_graph.pb"
)
TF_SSD_V3_PBTXT_URL = (
    "https://gist.githubusercontent.com/dkurt/54a8e8b51beb3bd3f770b79e56927bd7/raw/"
    "ssd_mobilenet_v3_large_coco_2020_01_14.pbtxt"
)
TF_SSD_V3_MODEL_SHA256 = "3c95e720eed1bbaf264048ab8fbe6765e5b3a64fafe64020cd53ecd14ccf2c58"
TF_SSD_V3_PBTXT_SHA256 = "1b66fa9884a25a1a12ab688b8c5fc4a41143d2111d89f7cd1c1536707a3ef1f6"

COCO_CLASS_NAMES = {
    1: "person",
    2: "bicycle",
    3: "car",
    4: "motorcycle",
    6: "bus",
    8: "truck",
}
ROAD_VEHICLE_LABELS = {"car", "motorcycle", "bus", "truck"}


@dataclass(slots=True)
class VehicleDetectorConfig:
    model_dir: str = "data/models/ssd_mobilenet_v3_large_coco_2020_01_14"
    confidence_threshold: float = 0.35
    download_allowed: bool = True
    model_url: str = TF_SSD_V3_MODEL_URL
    pbtxt_url: str = TF_SSD_V3_PBTXT_URL
    model_sha256: str = TF_SSD_V3_MODEL_SHA256
    pbtxt_sha256: str = TF_SSD_V3_PBTXT_SHA256


class VehicleDetector:
    def __init__(self, config: VehicleDetectorConfig) -> None:
        self.config = config
        self._net = None
        self._weights_path, self._pbtxt_path = ensure_vehicle_model_assets(
            Path(config.model_dir),
            download_allowed=config.download_allowed,
            model_url=config.model_url,
            pbtxt_url=config.pbtxt_url,
            model_sha256=config.model_sha256,
            pbtxt_sha256=config.pbtxt_sha256,
        )

    def detect(self, frame_bgr: np.ndarray) -> list[VehicleDetection]:
        if self._net is None:
            self._net = cv2.dnn.readNetFromTensorflow(str(self._weights_path), str(self._pbtxt_path))
        net = self._net
        height, width = frame_bgr.shape[:2]
        net.setInput(cv2.dnn.blobFromImage(frame_bgr, size=(320, 320), swapRB=True, crop=False))
        out = net.forward()
        detections: list[VehicleDetection] = []
        for detection in out[0, 0, :, :]:
            score = float(detection[2])
            if score < self.config.confidence_threshold:
                continue
            class_id = int(detection[1])
            label = COCO_CLASS_NAMES.get(class_id)
            if label not in ROAD_VEHICLE_LABELS:
                continue
            left = max(0, int(detection[3] * width))
            top = max(0, int(detection[4] * height))
            right = min(width, int(detection[5] * width))
            bottom = min(height, int(detection[6] * height))
            if right <= left or bottom <= top:
                continue
            area = float((right - left) * (bottom - top))
            center_x = float((left + right) / 2.0)
            detections.append(VehicleDetection(label, score, (left, top, right, bottom), area, center_x))
        return detections


def select_lead_vehicle(
    detections: list[VehicleDetection],
    *,
    frame_width: int,
    frame_height: int,
) -> LeadVehicleObservation | None:
    if not detections:
        return None
    frame_center_x = frame_width / 2.0

    def score(det: VehicleDetection) -> tuple[float, float]:
        left, top, right, bottom = det.box
        bottom_bias = bottom / max(frame_height, 1)
        center_penalty = abs(det.center_x_px - frame_center_x)
        return (bottom_bias * det.area_px * det.confidence, -center_penalty)

    best = max(detections, key=score)
    left, top, right, bottom = best.box
    return LeadVehicleObservation(
        label=best.label,
        confidence=best.confidence,
        box=best.box,
        area_px=best.area_px,
        center_x_px=best.center_x_px,
        bottom_y_px=float(bottom),
    )


def ensure_vehicle_model_assets(
    model_dir: Path,
    *,
    download_allowed: bool,
    model_url: str,
    pbtxt_url: str,
    model_sha256: str,
    pbtxt_sha256: str,
) -> tuple[Path, Path]:
    model_dir.mkdir(parents=True, exist_ok=True)
    weights = model_dir / "frozen_inference_graph.pb"
    pbtxt = model_dir / "graph.pbtxt"
    if weights.exists() and pbtxt.exists():
        if model_sha256:
            _verify_checksum(weights, model_sha256)
        if pbtxt_sha256:
            _verify_checksum(pbtxt, pbtxt_sha256)
        return weights, pbtxt
    if not download_allowed:
        raise RuntimeError("vehicle model assets are missing and download is disabled")
    download_file(model_url, weights, expected_sha256=model_sha256)
    download_file(pbtxt_url, pbtxt, expected_sha256=pbtxt_sha256)
    return weights, pbtxt


def download_file(url: str, destination: Path, *, expected_sha256: str = "") -> None:
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(response.content)
    _verify_checksum(destination, expected_sha256)


def _verify_checksum(path: Path, expected_sha256: str) -> None:
    if expected_sha256:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != expected_sha256:
            raise RuntimeError(
                f"checksum mismatch for {path.name}: expected {expected_sha256}, got {digest}"
            )
