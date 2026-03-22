from __future__ import annotations

from ats_cinepilot.domain.types import RouteHint, VehicleCommand


def build_vehicle_command(
    steering: float,
    throttle: float,
    brake: float,
    hint: RouteHint | None = None,
) -> VehicleCommand:
    left = False
    right = False
    if hint and hint.confidence > 0.5:
        if hint.turn_bias < -0.4:
            left = True
        elif hint.turn_bias > 0.4:
            right = True
    return VehicleCommand(
        steering=steering,
        throttle=throttle,
        brake=brake,
        left_blinker=left,
        right_blinker=right,
    ).clipped()
