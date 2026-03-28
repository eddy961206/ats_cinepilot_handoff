from __future__ import annotations

from dataclasses import dataclass

from ats_cinepilot.bridge.keyboard_controls import KeyboardControlConfig, KeyboardControlSink
from ats_cinepilot.bridge.scs_controls import DynamicModuleControlSink, ModuleControlConfig
from ats_cinepilot.domain.types import VehicleCommand


@dataclass(slots=True)
class HybridControlConfig:
    module: ModuleControlConfig
    keyboard: KeyboardControlConfig


class ModuleSteeringKeyboardLongitudinalSink:
    """
    Demo-only split sink.

    - steering / blinkers: semantical control module
    - throttle / brake: focused keyboard injection
    """

    def __init__(self, config: HybridControlConfig, *, keyboard_emitter=None) -> None:
        self.config = config
        self.module_sink = DynamicModuleControlSink(config.module)
        self.keyboard_sink = KeyboardControlSink(config.keyboard, emitter=keyboard_emitter)

    def connect(self) -> None:
        self.module_sink.connect()
        try:
            self.keyboard_sink.connect()
        except Exception:
            self.module_sink.neutralize()
            raise

    def is_healthy(self) -> bool:
        return self.module_sink.is_healthy() and self.keyboard_sink.is_healthy()

    def apply(self, command: VehicleCommand) -> None:
        clipped = command.clipped()
        steering_command = VehicleCommand(
            steering=clipped.steering,
            throttle=0.0,
            brake=0.0,
            left_blinker=clipped.left_blinker,
            right_blinker=clipped.right_blinker,
        )
        longitudinal_command = VehicleCommand(
            steering=0.0,
            throttle=clipped.throttle,
            brake=clipped.brake,
            left_blinker=False,
            right_blinker=False,
        )
        self.module_sink.apply(steering_command)
        try:
            self.keyboard_sink.apply(longitudinal_command)
        except Exception:
            self.module_sink.neutralize()
            raise

    def neutralize(self) -> None:
        self.keyboard_sink.neutralize()
        self.module_sink.neutralize()
