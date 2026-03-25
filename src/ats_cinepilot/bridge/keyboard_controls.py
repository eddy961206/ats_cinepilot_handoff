from __future__ import annotations

import ctypes
import platform
from dataclasses import dataclass
from ctypes import wintypes

from ats_cinepilot.domain.types import VehicleCommand


ULONG_PTR = wintypes.WPARAM


class _KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class _MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class _HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ("uMsg", wintypes.DWORD),
        ("wParamL", wintypes.WORD),
        ("wParamH", wintypes.WORD),
    ]


class _INPUT_UNION(ctypes.Union):
    _fields_ = [
        ("ki", _KEYBDINPUT),
        ("mi", _MOUSEINPUT),
        ("hi", _HARDWAREINPUT),
    ]


class _INPUT(ctypes.Structure):
    _anonymous_ = ("u",)
    _fields_ = [("type", wintypes.DWORD), ("u", _INPUT_UNION)]


@dataclass(slots=True)
class KeyboardControlConfig:
    steer_left_key: str = "a"
    steer_right_key: str = "d"
    throttle_key: str = "w"
    brake_key: str = "s"
    steering_threshold: float = 0.15
    throttle_threshold: float = 0.08
    brake_threshold: float = 0.08


class WindowsKeyboardEmitter:
    _INPUT_KEYBOARD = 1
    _KEYEVENTF_SCANCODE = 0x0008
    _KEYEVENTF_KEYUP = 0x0002
    _SCAN_CODES = {
        "a": 0x1E,
        "d": 0x20,
        "s": 0x1F,
        "w": 0x11,
    }

    def __init__(self) -> None:
        self.user32 = ctypes.WinDLL("user32", use_last_error=True)

    def set_key_state(self, key: str, pressed: bool) -> None:
        scan_code = self._SCAN_CODES.get(key.lower())
        if scan_code is None:
            raise ValueError(f"unsupported keyboard control key: {key}")
        flags = self._KEYEVENTF_SCANCODE
        if not pressed:
            flags |= self._KEYEVENTF_KEYUP
        payload = _INPUT(
            type=self._INPUT_KEYBOARD,
            ki=_KEYBDINPUT(
                wVk=0,
                wScan=scan_code,
                dwFlags=flags,
                time=0,
                dwExtraInfo=0,
            ),
        )
        sent = self.user32.SendInput(1, ctypes.byref(payload), ctypes.sizeof(payload))
        if sent != 1:
            raise RuntimeError(
                f"SendInput failed for keyboard control (last_error={ctypes.get_last_error()})"
            )


class KeyboardControlSink:
    def __init__(self, config: KeyboardControlConfig, *, emitter=None) -> None:
        self.config = config
        self._emitter = emitter
        self._healthy = False
        self._pressed_keys: set[str] = set()

    def connect(self) -> None:
        if self._emitter is None:
            if platform.system() != "Windows":
                raise RuntimeError("keyboard control sink is Windows-only")
            self._emitter = WindowsKeyboardEmitter()
        self._healthy = True

    def is_healthy(self) -> bool:
        return self._healthy

    def apply(self, command: VehicleCommand) -> None:
        if not self._healthy or self._emitter is None:
            raise RuntimeError("keyboard control sink not connected")
        desired_keys = self._desired_keys(command.clipped())
        current_pressed = set(self._pressed_keys)
        try:
            for key in sorted(current_pressed - desired_keys):
                self._emitter.set_key_state(key, False)
                current_pressed.discard(key)
            for key in sorted(desired_keys - current_pressed):
                self._emitter.set_key_state(key, True)
                current_pressed.add(key)
            self._pressed_keys = current_pressed
        except Exception:
            self._release_best_effort(self._all_control_keys() | current_pressed | desired_keys)
            self._pressed_keys.clear()
            raise

    def neutralize(self) -> None:
        if self._emitter is None:
            return
        self._release_best_effort(self._pressed_keys)
        self._pressed_keys.clear()

    def _desired_keys(self, command: VehicleCommand) -> set[str]:
        desired: set[str] = set()
        if command.brake >= self.config.brake_threshold:
            desired.add(self.config.brake_key.lower())
        elif command.throttle >= self.config.throttle_threshold:
            desired.add(self.config.throttle_key.lower())

        if command.steering >= self.config.steering_threshold:
            desired.add(self.config.steer_left_key.lower())
        elif command.steering <= -self.config.steering_threshold:
            desired.add(self.config.steer_right_key.lower())
        return desired

    def _all_control_keys(self) -> set[str]:
        return {
            self.config.steer_left_key.lower(),
            self.config.steer_right_key.lower(),
            self.config.throttle_key.lower(),
            self.config.brake_key.lower(),
        }

    def _release_best_effort(self, keys: set[str]) -> None:
        for key in sorted(keys):
            try:
                self._emitter.set_key_state(key, False)
            except Exception:
                continue
