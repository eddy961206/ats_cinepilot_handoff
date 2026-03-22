from __future__ import annotations


def hud_confidence(route_pixels: int, min_route_pixels: int) -> float:
    if route_pixels <= 0:
        return 0.0
    if route_pixels >= min_route_pixels:
        return 1.0
    return max(0.0, min(1.0, route_pixels / float(max(min_route_pixels, 1))))


def fused_confidence(
    map_match_confidence: float,
    hud_conf: float,
    path_overlap: float,
    heading_consistency: float,
) -> float:
    score = (
        0.40 * map_match_confidence +
        0.30 * hud_conf +
        0.20 * path_overlap +
        0.10 * heading_consistency
    )
    return max(0.0, min(1.0, score))
