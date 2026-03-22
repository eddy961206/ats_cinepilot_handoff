from __future__ import annotations

from dataclasses import dataclass

from .enums import DisengageReason, Mode


@dataclass
class AutopilotStateMachine:
    mode: Mode = Mode.OFF
    disengage_reason: DisengageReason = DisengageReason.NONE

    def set_mode(self, mode: Mode, reason: DisengageReason = DisengageReason.NONE) -> None:
        self.mode = mode
        self.disengage_reason = reason

    def can_control(self) -> bool:
        return self.mode in {Mode.SHADOW, Mode.ACTIVE}

    def arm(self) -> None:
        self.mode = Mode.ARMED

    def activate(self) -> None:
        self.mode = Mode.ACTIVE

    def disengage(self, reason: DisengageReason) -> None:
        self.mode = Mode.DISENGAGING
        self.disengage_reason = reason

    def fault(self, reason: DisengageReason) -> None:
        self.mode = Mode.FAULT
        self.disengage_reason = reason
