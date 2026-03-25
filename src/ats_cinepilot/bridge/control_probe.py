from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable

from ats_cinepilot.domain.types import VehicleCommand


@dataclass(slots=True)
class ControlPulseRequest:
    axis: str
    value: float
    hold_s: float = 0.2


def build_pulse_command(axis: str, value: float) -> VehicleCommand:
    if axis == "steering":
        return VehicleCommand(steering=value, throttle=0.0, brake=0.0).clipped()
    if axis == "throttle":
        return VehicleCommand(steering=0.0, throttle=value, brake=0.0).clipped()
    if axis == "brake":
        return VehicleCommand(steering=0.0, throttle=0.0, brake=value).clipped()
    raise ValueError(f"unsupported control pulse axis: {axis}")


def run_control_pulse(
    sink,
    request: ControlPulseRequest,
    *,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> None:
    sink.apply(build_pulse_command(request.axis, request.value))
    try:
        sleep_fn(request.hold_s)
    finally:
        sink.neutralize()
