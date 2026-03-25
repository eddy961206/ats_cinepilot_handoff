from ats_cinepilot.bridge.keyboard_controls import KeyboardControlConfig, KeyboardControlSink
from ats_cinepilot.domain.types import VehicleCommand


class _FakeEmitter:
    def __init__(self) -> None:
        self.events: list[tuple[str, bool]] = []

    def set_key_state(self, key: str, pressed: bool) -> None:
        self.events.append((key, pressed))


def test_keyboard_control_sink_presses_expected_keys_for_command():
    emitter = _FakeEmitter()
    sink = KeyboardControlSink(
        KeyboardControlConfig(
            steer_left_key="a",
            steer_right_key="d",
            throttle_key="w",
            brake_key="s",
            steering_threshold=0.1,
            throttle_threshold=0.1,
            brake_threshold=0.1,
        ),
        emitter=emitter,
    )

    sink.connect()
    sink.apply(VehicleCommand(steering=0.2, throttle=0.3, brake=0.0))

    assert sink.is_healthy() is True
    assert emitter.events == [("a", True), ("w", True)]


def test_keyboard_control_sink_releases_old_keys_and_prioritizes_brake():
    emitter = _FakeEmitter()
    sink = KeyboardControlSink(KeyboardControlConfig(), emitter=emitter)

    sink.connect()
    sink.apply(VehicleCommand(steering=-0.2, throttle=0.3, brake=0.0))
    sink.apply(VehicleCommand(steering=0.0, throttle=0.3, brake=0.4))

    assert emitter.events == [("d", True), ("w", True), ("d", False), ("w", False), ("s", True)]


def test_keyboard_control_sink_neutralize_releases_pressed_keys():
    emitter = _FakeEmitter()
    sink = KeyboardControlSink(KeyboardControlConfig(), emitter=emitter)

    sink.connect()
    sink.apply(VehicleCommand(steering=-0.2, throttle=0.3, brake=0.0))
    sink.neutralize()

    assert emitter.events[-2:] == [("d", False), ("w", False)]
