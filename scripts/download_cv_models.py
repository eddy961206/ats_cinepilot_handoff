from __future__ import annotations

import argparse
from pathlib import Path

from ats_cinepilot.ops.config import cfg_get, resolve_config
from ats_cinepilot.perception.vehicle_detector import (
    TF_SSD_V3_MODEL_SHA256,
    TF_SSD_V3_MODEL_URL,
    TF_SSD_V3_PBTXT_SHA256,
    TF_SSD_V3_PBTXT_URL,
    ensure_vehicle_model_assets,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", action="append", default=[])
    parser.add_argument(
        "--model-dir",
        default="data/models/ssd_mobilenet_v3_large_coco_2020_01_14",
    )
    args = parser.parse_args()

    model_dir = Path(args.model_dir)
    model_url = TF_SSD_V3_MODEL_URL
    pbtxt_url = TF_SSD_V3_PBTXT_URL
    model_sha256 = TF_SSD_V3_MODEL_SHA256
    pbtxt_sha256 = TF_SSD_V3_PBTXT_SHA256
    if args.config:
        cfg = resolve_config(args.config)
        model_dir = Path(
            str(
                cfg_get(
                    cfg,
                    "cv.vehicles.model_dir",
                    model_dir,
                )
            )
        )
        model_url = str(cfg_get(cfg, "cv.vehicles.model_url", model_url))
        pbtxt_url = str(cfg_get(cfg, "cv.vehicles.pbtxt_url", pbtxt_url))
        model_sha256 = str(cfg_get(cfg, "cv.vehicles.model_sha256", model_sha256))
        pbtxt_sha256 = str(cfg_get(cfg, "cv.vehicles.pbtxt_sha256", pbtxt_sha256))

    weights, pbtxt = ensure_vehicle_model_assets(
        model_dir,
        download_allowed=True,
        model_url=model_url,
        pbtxt_url=pbtxt_url,
        model_sha256=model_sha256,
        pbtxt_sha256=pbtxt_sha256,
    )

    print(f"saved {weights}")
    print(f"saved {pbtxt}")


if __name__ == "__main__":
    main()
