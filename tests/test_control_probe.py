from ats_cinepilot.bridge.control_probe import ControlPulseRequest, build_pulse_command, run_control_pulse


class _FakeSink:
    def __init__(self) -> None:
        self.commands = []
        self.neutralized = 0

    def apply(self, command) -> None:
        self.commands.append(command)

    def neutralize(self) -> None:
        self.neutralized += 1


def test_build_pulse_command_sets_only_selected_axis():
    command = build_pulse_command("throttle", 0.25)

    assert command.steering == 0.0
    assert command.throttle == 0.25
    assert command.brake == 0.0


def test_run_control_pulse_applies_then_neutralizes():
    sink = _FakeSink()
    slept = []

    run_control_pulse(
        sink,
        ControlPulseRequest(axis="brake", value=0.1, hold_s=0.2),
        sleep_fn=lambda seconds: slept.append(seconds),
    )

    assert len(sink.commands) == 1
    assert sink.commands[0].brake == 0.1
    assert sink.neutralized == 1
    assert slept == [0.2]
