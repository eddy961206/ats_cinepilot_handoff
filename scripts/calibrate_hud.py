from __future__ import annotations

import argparse
from pathlib import Path

import cv2

from ats_cinepilot.ops.config import cfg_get, resolve_config
from ats_cinepilot.perception.hud_layout import crop_roi, denormalize_roi, load_preset
from ats_cinepilot.perception.route_mask import extract_route_mask


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", action="append", required=True)
    parser.add_argument("--image", required=True)
    parser.add_argument("--output-dir", default="data/calibrations")
    args = parser.parse_args()

    cfg = resolve_config(args.config)
    preset = load_preset(cfg_get(cfg, "hud.preset_path"))

    image = cv2.imread(args.image, cv2.IMREAD_COLOR)
    if image is None:
        raise FileNotFoundError(args.image)

    roi = denormalize_roi(image.shape, preset.normalized_roi)
    roi_img = crop_roi(image, roi)
    mask = extract_route_mask(roi_img, preset)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out_dir / "hud_roi.png"), roi_img)
    cv2.imwrite(str(out_dir / "hud_mask.png"), mask)
    print(f"saved calibration previews to {out_dir}")


if __name__ == "__main__":
    main()
