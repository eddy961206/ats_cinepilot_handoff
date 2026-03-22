import math
import struct

import pytest

from ats_cinepilot.bridge.scs_telemetry import (
    SharedMemoryV2Config,
    SharedMemoryV2DecodeError,
    SharedMemoryV2Decoder,
)
from ats_cinepilot.ops.config import validate_runtime_config


def _build_shared_memory_v2_buffer(
    *,
    state_code: float = 2.0,
    tick: float = 1000.0,
    velocity_x_mps: float = 3.0,
    velocity_z_mps: float = 4.0,
    speed_mps: float = 5.0,
    engine_rpm: float = 700.0,
    gear: int = 2,
    displayed_gear: int = 2,
    throttle: float = 0.15,
    speed_limit_kph: float = 72.0,
    route_distance_km: float = 12.5,
    route_time_min: float = 18.0,
) -> bytes:
    buf = bytearray(1024)
    buf[1:4] = b"ats"
    struct.pack_into("<f", buf, 44, state_code)
    struct.pack_into("<f", buf, 296, tick)
    struct.pack_into("<f", buf, 333, velocity_x_mps)
    struct.pack_into("<f", buf, 357, velocity_z_mps)
    struct.pack_into("<f", buf, 445, speed_mps)
    struct.pack_into("<f", buf, 449, engine_rpm)
    struct.pack_into("<I", buf, 453, gear)
    struct.pack_into("<I", buf, 457, displayed_gear)
    struct.pack_into("<f", buf, 461, throttle)
    struct.pack_into("<f", buf, 507, speed_limit_kph)
    struct.pack_into("<f", buf, 544, route_distance_km)
    struct.pack_into("<f", buf, 548, route_time_min)
    return bytes(buf)


def test_shared_memory_v2_decoder_emits_relative_pose_and_diagnostics():
    decoder = SharedMemoryV2Decoder(SharedMemoryV2Config())

    frame1 = decoder.decode(_build_shared_memory_v2_buffer(), mono_time_s=10.0)
    frame2 = decoder.decode(_build_shared_memory_v2_buffer(tick=1005.0), mono_time_s=10.5)

    assert frame1.paused is False
    assert frame1.game_tick != frame2.game_tick
    assert frame1.speed_mps == pytest.approx(5.0)
    assert frame1.speed_limit_mps == pytest.approx(20.0)
    assert frame1.nav_distance_m is None
    assert frame1.pose.world_x == pytest.approx(0.0)
    assert frame1.pose.world_z == pytest.approx(0.0)
    assert frame1.pose.yaw_rad == pytest.approx(math.atan2(4.0, 3.0))

    assert frame2.pose.world_x == pytest.approx(1.5)
    assert frame2.pose.world_z == pytest.approx(2.0)
    assert frame2.pose.yaw_rad == pytest.approx(math.atan2(4.0, 3.0))

    assert decoder.last_state is not None
    assert decoder.last_state.tick_candidate == pytest.approx(1005.0)
    assert decoder.last_state.update_token == frame2.game_tick
    assert decoder.last_state.engine_rpm == pytest.approx(700.0)
    assert decoder.last_state.gear == 2
    assert decoder.last_state.displayed_gear == 2
    assert decoder.last_state.throttle == pytest.approx(0.15)
    assert decoder.last_state.route_distance_km_candidate == pytest.approx(12.5)
    assert decoder.last_state.route_time_min_candidate == pytest.approx(18.0)


def test_shared_memory_v2_decoder_rejects_wrong_game_tag():
    decoder = SharedMemoryV2Decoder(SharedMemoryV2Config())
    buf = bytearray(_build_shared_memory_v2_buffer())
    buf[1:4] = b"ets"

    with pytest.raises(SharedMemoryV2DecodeError):
        decoder.decode(bytes(buf), mono_time_s=10.0)


def test_validate_runtime_config_accepts_shared_memory_v2():
    issues = validate_runtime_config(
        {
            "map": {"cache_path": "data/maps/cache/default_graph.json"},
            "telemetry": {"source": "shared_memory_v2"},
            "control": {"sink": "noop"},
            "hud": {"preset_path": ""},
        },
        mode="shadow",
    )

    assert issues == []
