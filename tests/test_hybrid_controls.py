from pathlib import Path

from ats_cinepilot.bridge.hybrid_controls import HybridControlConfig, ModuleSteeringKeyboardLongitudinalSink
from ats_cinepilot.bridge.keyboard_controls import KeyboardControlConfig
from ats_cinepilot.bridge.scs_controls import ModuleControlConfig
from ats_cinepilot.domain.types import VehicleCommand


class FakeEmitter:
    def __init__(self) -> None:
        self.events: list[tuple[str, bool]] = []

    def set_key_state(self, key: str, pressed: bool) -> None:
        self.events.append((key, pressed))


def test_hybrid_sink_routes_steering_to_module_and_longitudinal_to_keyboard(tmp_path: Path):
    module_path = tmp_path / "demo_control_module_hybrid_route.py"
    module_path.write_text(
        "\n".join(
            [
                "class DemoController:",
                "    steering: float = 0.0",
                "    aforward: float = 0.0",
                "    abackward: float = 0.0",
                "    lblinker: bool = False",
                "    rblinker: bool = False",
                "    def __init__(self):",
                "        self.steering = 0.0",
                "        self.aforward = 0.0",
                "        self.abackward = 0.0",
                "        self.lblinker = False",
                "        self.rblinker = False",
            ]
        ),
        encoding="utf-8",
    )
    emitter = FakeEmitter()
    sink = ModuleSteeringKeyboardLongitudinalSink(
        HybridControlConfig(
            module=ModuleControlConfig(
                module_name="demo_control_module_hybrid_route",
                class_name="DemoController",
                field_mapping={
                    "throttle": "aforward",
                    "brake": "abackward",
                    "left_blinker": "lblinker",
                    "right_blinker": "rblinker",
                },
                module_search_paths=[str(tmp_path)],
            ),
            keyboard=KeyboardControlConfig(),
        ),
        keyboard_emitter=emitter,
    )

    sink.connect()
    sink.apply(VehicleCommand(steering=0.25, throttle=0.4, brake=0.0, left_blinker=True))

    assert sink.module_sink._obj.steering == 0.25
    assert sink.module_sink._obj.aforward == 0.0
    assert sink.module_sink._obj.abackward == 0.0
    assert sink.module_sink._obj.lblinker is True
    assert emitter.events == [("w", True)]


def test_hybrid_sink_neutralize_releases_keyboard_and_module_outputs(tmp_path: Path):
    module_path = tmp_path / "demo_control_module_hybrid_neutral.py"
    module_path.write_text(
        "\n".join(
            [
                "class DemoController:",
                "    steering: float = 0.0",
                "    throttle: float = 0.0",
                "    brake: float = 0.0",
                "    def __init__(self):",
                "        self.steering = 0.0",
                "        self.throttle = 0.0",
                "        self.brake = 0.0",
            ]
        ),
        encoding="utf-8",
    )
    emitter = FakeEmitter()
    sink = ModuleSteeringKeyboardLongitudinalSink(
        HybridControlConfig(
            module=ModuleControlConfig(
                module_name="demo_control_module_hybrid_neutral",
                class_name="DemoController",
                module_search_paths=[str(tmp_path)],
            ),
            keyboard=KeyboardControlConfig(),
        ),
        keyboard_emitter=emitter,
    )

    sink.connect()
    sink.apply(VehicleCommand(steering=0.25, throttle=0.4, brake=0.0))
    sink.neutralize()

    assert sink.module_sink._obj.steering == 0.0
    assert sink.module_sink._obj.throttle == 0.0
    assert sink.module_sink._obj.brake == 0.0
    assert emitter.events == [("w", True), ("w", False)]
