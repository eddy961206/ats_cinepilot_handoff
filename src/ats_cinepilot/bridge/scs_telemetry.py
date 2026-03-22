from __future__ import annotations

import ctypes
import json
import math
import platform
import struct
import time
import zlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, Optional

import requests

from ats_cinepilot.domain.types import Pose2D, TelemetryFrame


FILE_MAP_READ = 0x0004


def _lookup_dotted(data: dict[str, Any], dotted: str, default: Any = None) -> Any:
    node: Any = data
    for part in dotted.split("."):
        if isinstance(node, dict) and part in node:
            node = node[part]
        else:
            return default
    return node


@dataclass
class JsonTelemetryConfig:
    endpoint: str
    timeout_s: float
    field_map: dict[str, str]


@dataclass(slots=True)
class SharedMemoryV2Config:
    mapping_name: str = "SCSTelemetrySharedv2_ats"
    expected_game_tag: str = "ats"
    min_mapping_size: int = 768
    in_world_state_code: float = 2.0
    state_code_offset: int = 44
    tick_offset: int = 296
    velocity_x_offset: int = 333
    velocity_z_offset: int = 357
    speed_mps_offset: int = 445
    engine_rpm_offset: int = 449
    gear_offset: int = 453
    displayed_gear_offset: int = 457
    throttle_offset: int = 461
    speed_limit_kph_offset: int = 507
    route_distance_km_offset: int = 544
    route_time_min_offset: int = 548
    absolute_x_offset: int | None = None
    absolute_y_offset: int | None = None
    absolute_z_offset: int | None = None
    absolute_value_format: str = "f64"
    pose_frame_mode: str = "anchored_local"
    heading_min_speed_mps: float = 0.25
    absolute_heading_min_distance_m: float = 0.25
    absolute_discontinuity_distance_m: float = 25.0


@dataclass(slots=True)
class SharedMemoryV2State:
    game_tag: str
    state_code: float
    tick_candidate: float
    update_token: int
    velocity_x_mps: float
    velocity_z_mps: float
    speed_mps: float
    engine_rpm: float
    gear: int
    displayed_gear: int
    throttle: float
    speed_limit_kph_candidate: float | None
    route_distance_km_candidate: float | None
    route_time_min_candidate: float | None
    pose_source: str = "relative_integrated_velocity"
    pose_frame: str = "integrated_velocity_local"
    heading_source: str = "velocity_direction"
    absolute_heading_rad: float | None = None
    anchor_heading_rad: float | None = None
    anchor_heading_locked: bool = False
    discontinuity_detected: bool = False
    discontinuity_distance_m: float | None = None
    anchor_reset_count: int = 0
    anchor_reset_reason: str | None = None
    absolute_world_x_m: float | None = None
    absolute_world_y_m: float | None = None
    absolute_world_z_m: float | None = None


class SharedMemoryV2AttachError(RuntimeError):
    pass


class SharedMemoryV2DecodeError(RuntimeError):
    pass


class HttpJsonTelemetrySource:
    """
    Generic JSON telemetry source.

    이 클래스는 특정 플러그인 스키마를 하드코딩하지 않는다.
    config의 dotted-path mapping을 통해 필수 필드를 끌어오는 방식이다.
    """

    def __init__(self, config: JsonTelemetryConfig) -> None:
        self.config = config
        self.session = requests.Session()
        self._healthy = False
        self._last_tick: int = 0

    def connect(self) -> None:
        self._healthy = True

    def is_healthy(self) -> bool:
        return self._healthy

    def read(self) -> Optional[TelemetryFrame]:
        try:
            resp = self.session.get(self.config.endpoint, timeout=self.config.timeout_s)
            resp.raise_for_status()
            payload = resp.json()
            self._healthy = True
        except Exception:
            self._healthy = False
            return None

        fmap = self.config.field_map
        tick = _lookup_dotted(payload, fmap.get("game_tick", ""), self._last_tick + 1)
        self._last_tick = int(tick)

        frame = TelemetryFrame(
            mono_time_s=time.monotonic(),
            game_tick=int(tick),
            paused=bool(_lookup_dotted(payload, fmap["paused"], False)),
            speed_mps=float(_lookup_dotted(payload, fmap["speed_mps"], 0.0) or 0.0),
            speed_limit_mps=_opt_float(_lookup_dotted(payload, fmap.get("speed_limit_mps", ""))),
            nav_distance_m=_opt_float(_lookup_dotted(payload, fmap.get("nav_distance_m", ""))),
            pose=Pose2D(
                world_x=float(_lookup_dotted(payload, fmap["pose.world_x"], 0.0) or 0.0),
                world_z=float(_lookup_dotted(payload, fmap["pose.world_z"], 0.0) or 0.0),
                yaw_rad=float(_lookup_dotted(payload, fmap["pose.yaw_rad"], 0.0) or 0.0),
            ),
        )
        return frame


class SharedMemoryV2Decoder:
    def __init__(self, config: SharedMemoryV2Config) -> None:
        self.config = config
        self.last_state: SharedMemoryV2State | None = None
        self._last_mono_time_s: float | None = None
        self._last_yaw_rad: float = 0.0
        self._pose_x_m: float = 0.0
        self._pose_z_m: float = 0.0
        self._anchor_absolute_x_m: float | None = None
        self._anchor_absolute_z_m: float | None = None
        self._anchor_heading_rad: float | None = None
        self._heading_reference_x_m: float | None = None
        self._heading_reference_z_m: float | None = None
        self._last_absolute_heading_rad: float | None = None
        self._last_absolute_sample_x_m: float | None = None
        self._last_absolute_sample_z_m: float | None = None
        self._anchor_reset_count: int = 0

    def decode(self, raw: bytes, mono_time_s: float | None = None) -> TelemetryFrame:
        game_tag = self._validate_buffer(raw)

        state_code = self._read_float32(raw, self.config.state_code_offset)
        tick_scalar = self._read_float32(raw, self.config.tick_offset)
        velocity_x_mps = self._read_float32(raw, self.config.velocity_x_offset)
        velocity_z_mps = self._read_float32(raw, self.config.velocity_z_offset)
        planar_speed_mps = math.hypot(velocity_x_mps, velocity_z_mps)
        speed_mps = abs(self._read_float32(raw, self.config.speed_mps_offset))
        if not math.isfinite(speed_mps) or speed_mps <= 0.0:
            speed_mps = planar_speed_mps
        engine_rpm = max(0.0, self._read_float32(raw, self.config.engine_rpm_offset))
        gear = self._read_u32(raw, self.config.gear_offset)
        displayed_gear = self._read_u32(raw, self.config.displayed_gear_offset)
        throttle = max(0.0, self._read_float32(raw, self.config.throttle_offset))
        speed_limit_kph = self._read_optional_float32(raw, self.config.speed_limit_kph_offset, 1.0, 200.0)
        route_distance_km = self._read_optional_float32(raw, self.config.route_distance_km_offset, 0.0, 5000.0)
        route_time_min = self._read_optional_float32(raw, self.config.route_time_min_offset, 0.0, 5000.0)

        mono_time_s = time.monotonic() if mono_time_s is None else mono_time_s
        dt = self._compute_dt(mono_time_s)
        self._pose_x_m += velocity_x_mps * dt
        self._pose_z_m += velocity_z_mps * dt

        velocity_heading_rad = None
        if planar_speed_mps >= self.config.heading_min_speed_mps:
            velocity_heading_rad = math.atan2(velocity_z_mps, velocity_x_mps)

        update_token = zlib.crc32(raw)
        game_tick = int(update_token)
        paused = self._infer_paused(
            state_code=state_code,
            planar_speed_mps=planar_speed_mps,
            speed_mps=speed_mps,
            engine_rpm=engine_rpm,
            throttle=throttle,
            displayed_gear=displayed_gear,
            route_distance_km=route_distance_km,
            route_time_min=route_time_min,
        )
        absolute_world_x_m = self._read_optional_position(raw, self.config.absolute_x_offset)
        absolute_world_y_m = self._read_optional_position(raw, self.config.absolute_y_offset)
        absolute_world_z_m = self._read_optional_position(raw, self.config.absolute_z_offset)
        discontinuity_detected = False
        discontinuity_distance_m = None
        anchor_reset_reason = None
        if absolute_world_x_m is not None and absolute_world_z_m is not None:
            discontinuity_distance_m, discontinuity_detected = self._check_absolute_discontinuity(
                absolute_world_x_m=absolute_world_x_m,
                absolute_world_z_m=absolute_world_z_m,
            )
            if discontinuity_detected:
                anchor_reset_reason = "absolute_position_jump"
                self._reset_absolute_tracking(
                    absolute_world_x_m=absolute_world_x_m,
                    absolute_world_z_m=absolute_world_z_m,
                )
        absolute_heading_rad = self._derive_absolute_heading(
            absolute_world_x_m=absolute_world_x_m,
            absolute_world_z_m=absolute_world_z_m,
        )
        heading_rad, heading_source = self._select_heading(
            absolute_heading_rad=absolute_heading_rad,
            velocity_heading_rad=velocity_heading_rad,
            absolute_position_available=absolute_world_x_m is not None and absolute_world_z_m is not None,
        )
        pose_x_m, pose_z_m, pose_yaw_rad, pose_frame, pose_source = self._select_pose(
            absolute_world_x_m=absolute_world_x_m,
            absolute_world_z_m=absolute_world_z_m,
            heading_rad=heading_rad,
            heading_source=heading_source,
        )
        self._last_yaw_rad = pose_yaw_rad
        frame = TelemetryFrame(
            mono_time_s=mono_time_s,
            game_tick=game_tick,
            paused=paused,
            speed_mps=speed_mps,
            speed_limit_mps=(speed_limit_kph / 3.6) if speed_limit_kph is not None else None,
            nav_distance_m=None,
            pose=Pose2D(
                world_x=pose_x_m,
                world_z=pose_z_m,
                yaw_rad=pose_yaw_rad,
            ),
        )
        self.last_state = SharedMemoryV2State(
            game_tag=game_tag,
            state_code=state_code,
            tick_candidate=tick_scalar,
            update_token=update_token,
            velocity_x_mps=velocity_x_mps,
            velocity_z_mps=velocity_z_mps,
            speed_mps=speed_mps,
            engine_rpm=engine_rpm,
            gear=gear,
            displayed_gear=displayed_gear,
            throttle=throttle,
            speed_limit_kph_candidate=speed_limit_kph,
            route_distance_km_candidate=route_distance_km,
            route_time_min_candidate=route_time_min,
            pose_source=pose_source,
            pose_frame=pose_frame,
            heading_source=heading_source,
            absolute_heading_rad=absolute_heading_rad,
            anchor_heading_rad=self._anchor_heading_rad,
            anchor_heading_locked=self._anchor_heading_rad is not None,
            discontinuity_detected=discontinuity_detected,
            discontinuity_distance_m=discontinuity_distance_m,
            anchor_reset_count=self._anchor_reset_count,
            anchor_reset_reason=anchor_reset_reason,
            absolute_world_x_m=absolute_world_x_m,
            absolute_world_y_m=absolute_world_y_m,
            absolute_world_z_m=absolute_world_z_m,
        )
        return frame

    def _compute_dt(self, mono_time_s: float) -> float:
        if self._last_mono_time_s is None or mono_time_s <= self._last_mono_time_s:
            self._last_mono_time_s = mono_time_s
            return 0.0

        dt = mono_time_s - self._last_mono_time_s
        self._last_mono_time_s = mono_time_s
        return min(dt, 0.5)

    def _validate_buffer(self, raw: bytes) -> str:
        if len(raw) < self.config.min_mapping_size:
            raise SharedMemoryV2DecodeError(
                f"shared memory buffer is too small: got {len(raw)} bytes, need {self.config.min_mapping_size}"
            )
        game_tag = raw[1:4].decode("ascii", errors="ignore")
        if game_tag != self.config.expected_game_tag:
            raise SharedMemoryV2DecodeError(
                f"unexpected shared memory game tag: {game_tag!r} != {self.config.expected_game_tag!r}"
            )
        return game_tag

    @staticmethod
    def _read_float32(raw: bytes, offset: int) -> float:
        try:
            value = struct.unpack_from("<f", raw, offset)[0]
        except struct.error as exc:
            raise SharedMemoryV2DecodeError(f"float32 read failed at offset {offset}") from exc
        if not math.isfinite(value):
            raise SharedMemoryV2DecodeError(f"non-finite float32 at offset {offset}")
        return value

    @staticmethod
    def _read_u32(raw: bytes, offset: int) -> int:
        try:
            return int(struct.unpack_from("<I", raw, offset)[0])
        except struct.error as exc:
            raise SharedMemoryV2DecodeError(f"uint32 read failed at offset {offset}") from exc

    def _read_optional_float32(self, raw: bytes, offset: int, minimum: float, maximum: float) -> float | None:
        value = self._read_float32(raw, offset)
        if value < minimum or value > maximum:
            return None
        return value

    def _read_optional_position(self, raw: bytes, offset: int | None) -> float | None:
        if offset is None:
            return None
        value = self._read_numeric(raw, offset, self.config.absolute_value_format)
        if value is None:
            return None
        if abs(value) > 1.0e9:
            return None
        return value

    def _read_numeric(self, raw: bytes, offset: int, value_format: str) -> float | None:
        try:
            if value_format == "f64":
                value = struct.unpack_from("<d", raw, offset)[0]
            elif value_format == "f32":
                value = struct.unpack_from("<f", raw, offset)[0]
            else:
                raise SharedMemoryV2DecodeError(f"unsupported numeric format: {value_format}")
        except struct.error as exc:
            raise SharedMemoryV2DecodeError(f"{value_format} read failed at offset {offset}") from exc
        if not math.isfinite(value):
            return None
        return float(value)

    def _derive_absolute_heading(
        self,
        *,
        absolute_world_x_m: float | None,
        absolute_world_z_m: float | None,
    ) -> float | None:
        if absolute_world_x_m is None or absolute_world_z_m is None:
            self._heading_reference_x_m = None
            self._heading_reference_z_m = None
            return None

        if self._heading_reference_x_m is None or self._heading_reference_z_m is None:
            self._heading_reference_x_m = absolute_world_x_m
            self._heading_reference_z_m = absolute_world_z_m
            return None

        dx = absolute_world_x_m - self._heading_reference_x_m
        dz = absolute_world_z_m - self._heading_reference_z_m
        if math.hypot(dx, dz) < self.config.absolute_heading_min_distance_m:
            return None

        self._heading_reference_x_m = absolute_world_x_m
        self._heading_reference_z_m = absolute_world_z_m
        self._last_absolute_heading_rad = math.atan2(dz, dx)
        return self._last_absolute_heading_rad

    def _check_absolute_discontinuity(
        self,
        *,
        absolute_world_x_m: float,
        absolute_world_z_m: float,
    ) -> tuple[float | None, bool]:
        if self._last_absolute_sample_x_m is None or self._last_absolute_sample_z_m is None:
            self._last_absolute_sample_x_m = absolute_world_x_m
            self._last_absolute_sample_z_m = absolute_world_z_m
            return None, False

        distance_m = math.hypot(
            absolute_world_x_m - self._last_absolute_sample_x_m,
            absolute_world_z_m - self._last_absolute_sample_z_m,
        )
        self._last_absolute_sample_x_m = absolute_world_x_m
        self._last_absolute_sample_z_m = absolute_world_z_m
        return distance_m, distance_m >= self.config.absolute_discontinuity_distance_m

    def _reset_absolute_tracking(
        self,
        *,
        absolute_world_x_m: float,
        absolute_world_z_m: float,
    ) -> None:
        self._anchor_absolute_x_m = absolute_world_x_m
        self._anchor_absolute_z_m = absolute_world_z_m
        self._anchor_heading_rad = None
        self._heading_reference_x_m = absolute_world_x_m
        self._heading_reference_z_m = absolute_world_z_m
        self._last_absolute_heading_rad = None
        self._anchor_reset_count += 1

    def _select_heading(
        self,
        *,
        absolute_heading_rad: float | None,
        velocity_heading_rad: float | None,
        absolute_position_available: bool,
    ) -> tuple[float, str]:
        if absolute_heading_rad is not None:
            return absolute_heading_rad, "absolute_position_delta"
        if absolute_position_available and self._last_absolute_heading_rad is not None:
            return self._last_absolute_heading_rad, "absolute_position_hold"
        if velocity_heading_rad is not None:
            return velocity_heading_rad, "velocity_direction"
        return self._last_yaw_rad, "unknown"

    def _select_pose(
        self,
        *,
        absolute_world_x_m: float | None,
        absolute_world_z_m: float | None,
        heading_rad: float,
        heading_source: str,
    ) -> tuple[float, float, float, str, str]:
        if absolute_world_x_m is None or absolute_world_z_m is None:
            return (
                self._pose_x_m,
                self._pose_z_m,
                heading_rad,
                "integrated_velocity_local",
                "relative_integrated_velocity",
            )

        if self.config.pose_frame_mode == "world_absolute":
            return absolute_world_x_m, absolute_world_z_m, heading_rad, "world_absolute", "authoritative_absolute"

        if self.config.pose_frame_mode == "anchored_local":
            if self._anchor_absolute_x_m is None or self._anchor_absolute_z_m is None:
                self._anchor_absolute_x_m = absolute_world_x_m
                self._anchor_absolute_z_m = absolute_world_z_m
            if self._anchor_heading_rad is None and heading_source == "absolute_position_delta":
                self._anchor_heading_rad = heading_rad
            dx = absolute_world_x_m - self._anchor_absolute_x_m
            dz = absolute_world_z_m - self._anchor_absolute_z_m
            anchor_heading_rad = self._anchor_heading_rad if self._anchor_heading_rad is not None else heading_rad
            local_x, local_z = _rotate_into_local_frame(dx, dz, anchor_heading_rad)
            if self._anchor_heading_rad is None:
                return local_x, local_z, 0.0, "anchored_local_pending_heading", "authoritative_absolute"
            local_yaw_rad = _normalize_angle_rad(heading_rad - self._anchor_heading_rad)
            return local_x, local_z, local_yaw_rad, "anchored_local", "authoritative_absolute"

        raise SharedMemoryV2DecodeError(f"unsupported pose_frame_mode: {self.config.pose_frame_mode}")

    def _infer_paused(
        self,
        *,
        state_code: float,
        planar_speed_mps: float,
        speed_mps: float,
        engine_rpm: float,
        throttle: float,
        displayed_gear: int,
        route_distance_km: float | None,
        route_time_min: float | None,
    ) -> bool:
        if (
            speed_mps > 0.05
            or planar_speed_mps > 0.05
            or engine_rpm > 100.0
            or throttle > 0.05
            or displayed_gear > 0
            or route_distance_km is not None
            or route_time_min is not None
        ):
            return False
        return not math.isclose(
            state_code,
            self.config.in_world_state_code,
            abs_tol=0.25,
        )


def _rotate_into_local_frame(world_dx_m: float, world_dz_m: float, anchor_heading_rad: float) -> tuple[float, float]:
    cos_yaw = math.cos(anchor_heading_rad)
    sin_yaw = math.sin(anchor_heading_rad)
    local_x = world_dx_m * cos_yaw + world_dz_m * sin_yaw
    local_z = -world_dx_m * sin_yaw + world_dz_m * cos_yaw
    return local_x, local_z


def _normalize_angle_rad(value: float) -> float:
    return (value + math.pi) % (2.0 * math.pi) - math.pi


class _WindowsNamedMappingReader:
    def __init__(self, name: str, minimum_size: int) -> None:
        self.name = name
        self.minimum_size = minimum_size
        self._kernel32 = None
        self._handle: int | None = None
        self._view: int | None = None
        self._size: int | None = None

    def connect(self) -> None:
        if platform.system() != "Windows":
            raise SharedMemoryV2AttachError("shared_memory_v2 telemetry is Windows-only")

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.OpenFileMappingW.argtypes = [ctypes.c_uint32, ctypes.c_int, ctypes.c_wchar_p]
        kernel32.OpenFileMappingW.restype = ctypes.c_void_p
        kernel32.MapViewOfFile.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_size_t]
        kernel32.MapViewOfFile.restype = ctypes.c_void_p
        kernel32.UnmapViewOfFile.argtypes = [ctypes.c_void_p]
        kernel32.UnmapViewOfFile.restype = ctypes.c_int
        kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
        kernel32.CloseHandle.restype = ctypes.c_int
        kernel32.VirtualQuery.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t]
        kernel32.VirtualQuery.restype = ctypes.c_size_t

        handle = kernel32.OpenFileMappingW(FILE_MAP_READ, False, self.name)
        if not handle:
            raise SharedMemoryV2AttachError(
                f"OpenFileMappingW failed for {self.name} with WinError {ctypes.get_last_error()}"
            )

        view = kernel32.MapViewOfFile(handle, FILE_MAP_READ, 0, 0, 0)
        if not view:
            kernel32.CloseHandle(handle)
            raise SharedMemoryV2AttachError(
                f"MapViewOfFile failed for {self.name} with WinError {ctypes.get_last_error()}"
            )

        size = self._query_region_size(kernel32, view)
        if size < self.minimum_size:
            kernel32.UnmapViewOfFile(view)
            kernel32.CloseHandle(handle)
            raise SharedMemoryV2AttachError(
                f"shared memory region is too small: got {size} bytes, need {self.minimum_size}"
            )

        self._kernel32 = kernel32
        self._handle = handle
        self._view = view
        self._size = size

    def read(self) -> bytes:
        if self._view is None or self._size is None:
            raise SharedMemoryV2AttachError("shared memory mapping is not connected")
        return ctypes.string_at(self._view, self._size)

    def close(self) -> None:
        if self._kernel32 is not None and self._view is not None:
            self._kernel32.UnmapViewOfFile(self._view)
        if self._kernel32 is not None and self._handle is not None:
            self._kernel32.CloseHandle(self._handle)
        self._handle = None
        self._view = None
        self._size = None

    @staticmethod
    def _query_region_size(kernel32: Any, view: int) -> int:
        class MEMORY_BASIC_INFORMATION(ctypes.Structure):
            _fields_ = [
                ("BaseAddress", ctypes.c_void_p),
                ("AllocationBase", ctypes.c_void_p),
                ("AllocationProtect", ctypes.c_uint32),
                ("PartitionId", ctypes.c_uint16),
                ("RegionSize", ctypes.c_size_t),
                ("State", ctypes.c_uint32),
                ("Protect", ctypes.c_uint32),
                ("Type", ctypes.c_uint32),
            ]

        mbi = MEMORY_BASIC_INFORMATION()
        result = kernel32.VirtualQuery(view, ctypes.byref(mbi), ctypes.sizeof(mbi))
        if not result:
            raise SharedMemoryV2AttachError(
                f"VirtualQuery failed with WinError {ctypes.get_last_error()}"
            )
        return int(mbi.RegionSize)


class SharedMemoryV2TelemetrySource:
    def __init__(self, config: SharedMemoryV2Config) -> None:
        self.config = config
        self.decoder = SharedMemoryV2Decoder(config)
        self.mapping = _WindowsNamedMappingReader(config.mapping_name, config.min_mapping_size)
        self._healthy = False
        self._primed_frame: TelemetryFrame | None = None
        self.last_error: str | None = None

    @property
    def last_state(self) -> SharedMemoryV2State | None:
        return self.decoder.last_state

    def connect(self) -> None:
        self.mapping.connect()
        try:
            self._primed_frame = self.decoder.decode(self.mapping.read())
        except Exception as exc:
            self.mapping.close()
            self.last_error = str(exc)
            raise SharedMemoryV2AttachError(str(exc)) from exc
        self._healthy = True
        self.last_error = None

    def is_healthy(self) -> bool:
        return self._healthy

    def read(self) -> Optional[TelemetryFrame]:
        if self._primed_frame is not None:
            frame = self._primed_frame
            self._primed_frame = None
            return frame

        try:
            frame = self.decoder.decode(self.mapping.read())
            self._healthy = True
            self.last_error = None
            return frame
        except Exception as exc:
            self._healthy = False
            self.last_error = str(exc)
            return None

    def read_raw(self) -> bytes:
        return self.mapping.read()

    def close(self) -> None:
        self.mapping.close()


def _opt_float(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


class ReplayTelemetrySource:
    def __init__(self, replay_path: str | Path) -> None:
        self.replay_path = Path(replay_path)
        self._frames: list[TelemetryFrame] = []
        self._iter: Optional[Iterator[TelemetryFrame]] = None
        self._healthy = False

    def connect(self) -> None:
        self._frames = list(self._load_frames())
        self._iter = iter(self._frames)
        self._healthy = True

    def is_healthy(self) -> bool:
        return self._healthy

    def read(self) -> Optional[TelemetryFrame]:
        if self._iter is None:
            return None
        try:
            return next(self._iter)
        except StopIteration:
            return None

    def _load_frames(self) -> Iterator[TelemetryFrame]:
        with self.replay_path.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                row = json.loads(line)
                pose = row["pose"]
                yield TelemetryFrame(
                    mono_time_s=float(row["mono_time_s"]),
                    game_tick=int(row["game_tick"]),
                    paused=bool(row["paused"]),
                    speed_mps=float(row["speed_mps"]),
                    speed_limit_mps=_opt_float(row.get("speed_limit_mps")),
                    nav_distance_m=_opt_float(row.get("nav_distance_m")),
                    pose=Pose2D(
                        world_x=float(pose["world_x"]),
                        world_z=float(pose["world_z"]),
                        yaw_rad=float(pose["yaw_rad"]),
                    ),
                )


class NullTelemetrySource:
    def connect(self) -> None:
        return None

    def is_healthy(self) -> bool:
        return True

    def read(self) -> Optional[TelemetryFrame]:
        return None
