from pathlib import Path

from ats_cinepilot.bridge.scs_controls import DynamicModuleControlSink, ModuleControlConfig
from ats_cinepilot.domain.types import VehicleCommand


def test_dynamic_module_control_sink_imports_from_configured_search_path(tmp_path: Path):
    module_path = tmp_path / "demo_control_module.py"
    module_path.write_text(
        "\n".join(
            [
                "class DemoController:",
                "    steering: float = 0.0",
                "    throttle: float = 0.0",
                "    brake: float = 0.0",
                "    left_blinker: bool = False",
                "    right_blinker: bool = False",
                "    def __init__(self):",
                "        self.steering = 0.0",
                "        self.throttle = 0.0",
                "        self.brake = 0.0",
                "        self.left_blinker = False",
                "        self.right_blinker = False",
            ]
        ),
        encoding="utf-8",
    )

    sink = DynamicModuleControlSink(
        ModuleControlConfig(
            module_name="demo_control_module",
            class_name="DemoController",
            module_search_paths=[str(tmp_path)],
        )
    )

    sink.connect()
    sink.apply(VehicleCommand(steering=0.2, throttle=0.3, brake=0.1, left_blinker=True))

    assert sink.is_healthy() is True
    assert sink._obj.steering == 0.2
    assert sink._obj.throttle == 0.3
    assert sink._obj.brake == 0.1
    assert sink._obj.left_blinker is True
