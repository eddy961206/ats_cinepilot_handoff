from ats_cinepilot.bridge.keyboard_controls import KeyboardControlConfig, KeyboardControlSink
from ats_cinepilot.domain.types import VehicleCommand


class _FakeEmitter:
    def __init__(self) -> None:
        self.events: list[tuple[str, bool]] = []

    def set_key_state(self, key: str, pressed: bool) -> None:
        self.events.append((key, pressed))


class _FailingEmitter(_FakeEmitter):
    def __init__(self, *, fail_on: tuple[str, bool]) -> None:
        super().__init__()
        self.fail_on = fail_on

    def set_key_state(self, key: str, pressed: bool) -> None:
        self.events.append((key, pressed))
        if (key, pressed) == self.fail_on:
            raise RuntimeError("injected failure")


class _FakeClock:
    def __init__(self, now_s: float = 0.0) -> None:
        self.now_s = now_s

    def __call__(self) -> float:
        return self.now_s


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


def test_keyboard_control_sink_releases_all_keys_when_transition_fails():
    emitter = _FailingEmitter(fail_on=("s", True))
    sink = KeyboardControlSink(KeyboardControlConfig(), emitter=emitter)

    sink.connect()
    sink.apply(VehicleCommand(steering=0.0, throttle=0.3, brake=0.0))

    try:
        sink.apply(VehicleCommand(steering=0.0, throttle=0.0, brake=0.4))
    except RuntimeError:
        pass
    else:
        raise AssertionError("expected transition failure")

    assert sink._pressed_keys == set()
    assert emitter.events == [
        ("w", True),
        ("w", False),
        ("s", True),
        ("a", False),
        ("d", False),
        ("s", False),
        ("w", False),
    ]


def test_keyboard_control_sink_pulses_longitudinal_key_when_pwm_enabled():
    emitter = _FakeEmitter()
    clock = _FakeClock(0.20)
    sink = KeyboardControlSink(
        KeyboardControlConfig(
            throttle_threshold=0.1,
            brake_threshold=0.1,
            longitudinal_pwm_period_s=1.0,
        ),
        emitter=emitter,
        clock=clock,
    )

    sink.connect()
    sink.apply(VehicleCommand(steering=0.0, throttle=0.3, brake=0.0))
    clock.now_s = 0.60
    sink.apply(VehicleCommand(steering=0.0, throttle=0.3, brake=0.0))

    assert emitter.events == [("w", True), ("w", False)]
