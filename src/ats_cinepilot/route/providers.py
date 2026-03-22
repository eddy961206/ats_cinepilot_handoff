from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ats_cinepilot.domain.types import MatchedEdge, RouteHint, TelemetryFrame
from ats_cinepilot.perception.confidence import hud_confidence
from ats_cinepilot.perception.hud_layout import crop_roi, denormalize_roi, load_preset
from ats_cinepilot.perception.nav_cue import estimate_turn_bias
from ats_cinepilot.perception.route_mask import extract_route_mask, route_pixel_count


@dataclass
class HudRouteProviderConfig:
    preset_path: str
    signature_check: bool = True


class HudRouteProvider:
    def __init__(self, capture_source, config: HudRouteProviderConfig) -> None:
        self.capture_source = capture_source
        self.preset = load_preset(config.preset_path)
        self.config = config

    def get_hint(
        self,
        frame: TelemetryFrame,
        matched: Optional[MatchedEdge],
    ) -> RouteHint:
        _ = frame, matched
        image = self.capture_source.grab()
        if image is None:
            return RouteHint(source="hud", turn_bias=0.0, path_overlap=0.0, next_branch_id=None, confidence=0.0)

        roi = denormalize_roi(image.shape, self.preset.normalized_roi)
        roi_img = crop_roi(image, roi)
        mask = extract_route_mask(roi_img, self.preset)
        pixels = route_pixel_count(mask)
        conf = hud_confidence(pixels, self.preset.min_route_pixels)
        bias = estimate_turn_bias(mask)
        return RouteHint(
            source="hud",
            turn_bias=bias,
            path_overlap=0.0,  # TODO: candidate branch와의 실제 overlap 계산은 로컬 codex가 붙일 것
            next_branch_id=None,
            confidence=conf,
        )


class DirectRouteProvider:
    def get_hint(
        self,
        frame: TelemetryFrame,
        matched: Optional[MatchedEdge],
    ) -> RouteHint:
        _ = frame, matched
        return RouteHint(source="direct", turn_bias=0.0, path_overlap=0.0, next_branch_id=None, confidence=0.0)


class NullRouteProvider:
    def get_hint(
        self,
        frame: TelemetryFrame,
        matched: Optional[MatchedEdge],
    ) -> RouteHint:
        _ = frame, matched
        return RouteHint(source="none", turn_bias=0.0, path_overlap=0.0, next_branch_id=None, confidence=0.0)
