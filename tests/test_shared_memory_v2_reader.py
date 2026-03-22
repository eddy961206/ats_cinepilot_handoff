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
    absolute_x_m: float | None = None,
    absolute_y_m: float | None = None,
    absolute_z_m: float | None = None,
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
    if absolute_x_m is not None:
        struct.pack_into("<d", buf, 285, absolute_x_m)
    if absolute_y_m is not None:
        struct.pack_into("<d", buf, 293, absolute_y_m)
    if absolute_z_m is not None:
        struct.pack_into("<d", buf, 301, absolute_z_m)
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


def test_shared_memory_v2_decoder_prefers_authoritative_absolute_pose_when_configured():
    decoder = SharedMemoryV2Decoder(
        SharedMemoryV2Config(
            absolute_x_offset=285,
            absolute_y_offset=293,
            absolute_z_offset=301,
            absolute_value_format="f64",
            pose_frame_mode="world_absolute",
        )
    )

    frame = decoder.decode(
        _build_shared_memory_v2_buffer(
            absolute_x_m=-67953.0,
            absolute_y_m=40.5,
            absolute_z_m=23734.7,
        ),
        mono_time_s=10.0,
    )

    assert frame.pose.world_x == pytest.approx(-67953.0)
    assert frame.pose.world_z == pytest.approx(23734.7)
    assert decoder.last_state is not None
    assert decoder.last_state.pose_source == "authoritative_absolute"
    assert decoder.last_state.pose_frame == "world_absolute"
    assert decoder.last_state.absolute_world_x_m == pytest.approx(-67953.0)
    assert decoder.last_state.absolute_world_y_m == pytest.approx(40.5)
    assert decoder.last_state.absolute_world_z_m == pytest.approx(23734.7)


def test_shared_memory_v2_decoder_can_anchor_authoritative_absolute_pose_to_local_frame():
    decoder = SharedMemoryV2Decoder(
        SharedMemoryV2Config(
            absolute_x_offset=285,
            absolute_z_offset=301,
            absolute_value_format="f64",
            pose_frame_mode="anchored_local",
        )
    )

    frame1 = decoder.decode(
        _build_shared_memory_v2_buffer(
            velocity_x_mps=4.0,
            velocity_z_mps=0.0,
            speed_mps=4.0,
            absolute_x_m=1000.0,
            absolute_z_m=2000.0,
        ),
        mono_time_s=10.0,
    )
    state_after_frame1 = decoder.last_state
    frame2 = decoder.decode(
        _build_shared_memory_v2_buffer(
            tick=1005.0,
            velocity_x_mps=4.0,
            velocity_z_mps=0.0,
            speed_mps=4.0,
            absolute_x_m=1008.0,
            absolute_z_m=2000.0,
        ),
        mono_time_s=12.0,
    )

    assert frame1.pose.world_x == pytest.approx(0.0)
    assert frame1.pose.world_z == pytest.approx(0.0)
    assert frame1.pose.yaw_rad == pytest.approx(0.0)
    assert state_after_frame1 is not None
    assert state_after_frame1.pose_frame == "anchored_local_pending_heading"
    assert state_after_frame1.anchor_heading_locked is False
    assert frame2.pose.world_x == pytest.approx(8.0)
    assert frame2.pose.world_z == pytest.approx(0.0, abs=1e-6)
    assert frame2.pose.yaw_rad == pytest.approx(0.0, abs=1e-6)
    assert decoder.last_state.pose_source == "authoritative_absolute"
    assert decoder.last_state.pose_frame == "anchored_local"
    assert decoder.last_state.heading_source == "absolute_position_delta"
    assert decoder.last_state.anchor_heading_locked is True


def test_shared_memory_v2_decoder_normalizes_local_yaw_against_anchor_heading():
    decoder = SharedMemoryV2Decoder(
        SharedMemoryV2Config(
            absolute_x_offset=285,
            absolute_z_offset=301,
            absolute_value_format="f64",
            pose_frame_mode="anchored_local",
        )
    )

    frame1 = decoder.decode(
        _build_shared_memory_v2_buffer(
            velocity_x_mps=-4.0,
            velocity_z_mps=0.0,
            speed_mps=4.0,
            absolute_x_m=1000.0,
            absolute_z_m=2000.0,
        ),
        mono_time_s=10.0,
    )
    frame2 = decoder.decode(
        _build_shared_memory_v2_buffer(
            tick=1005.0,
            velocity_x_mps=-4.0,
            velocity_z_mps=0.0,
            speed_mps=4.0,
            absolute_x_m=992.0,
            absolute_z_m=2000.0,
        ),
        mono_time_s=12.0,
    )

    assert frame1.pose.yaw_rad == pytest.approx(0.0, abs=1e-6)
    assert frame2.pose.world_x == pytest.approx(8.0)
    assert frame2.pose.yaw_rad == pytest.approx(0.0, abs=1e-6)


def test_shared_memory_v2_decoder_waits_for_absolute_heading_before_locking_anchor():
    decoder = SharedMemoryV2Decoder(
        SharedMemoryV2Config(
            absolute_x_offset=285,
            absolute_z_offset=301,
            absolute_value_format="f64",
            pose_frame_mode="anchored_local",
            absolute_heading_min_distance_m=0.5,
        )
    )

    frame1 = decoder.decode(
        _build_shared_memory_v2_buffer(
            velocity_x_mps=-1.0,
            velocity_z_mps=0.0,
            speed_mps=1.0,
            absolute_x_m=1000.0,
            absolute_z_m=2000.0,
        ),
        mono_time_s=10.0,
    )
    frame2 = decoder.decode(
        _build_shared_memory_v2_buffer(
            tick=1005.0,
            velocity_x_mps=-1.0,
            velocity_z_mps=0.0,
            speed_mps=1.0,
            absolute_x_m=999.0,
            absolute_z_m=1999.8,
        ),
        mono_time_s=11.0,
    )

    assert frame1.pose.world_x == pytest.approx(0.0)
    assert frame1.pose.world_z == pytest.approx(0.0)
    assert frame2.pose.world_x == pytest.approx(math.hypot(1.0, 0.2))
    assert frame2.pose.world_z == pytest.approx(0.0, abs=1e-6)
    assert decoder.last_state is not None
    assert decoder.last_state.heading_source == "absolute_position_delta"
    assert decoder.last_state.anchor_heading_locked is True


def test_shared_memory_v2_decoder_holds_last_absolute_heading_between_updates():
    decoder = SharedMemoryV2Decoder(
        SharedMemoryV2Config(
            absolute_x_offset=285,
            absolute_z_offset=301,
            absolute_value_format="f64",
            pose_frame_mode="anchored_local",
            absolute_heading_min_distance_m=0.5,
        )
    )

    decoder.decode(
        _build_shared_memory_v2_buffer(
            velocity_x_mps=-1.0,
            velocity_z_mps=0.0,
            speed_mps=1.0,
            absolute_x_m=1000.0,
            absolute_z_m=2000.0,
        ),
        mono_time_s=10.0,
    )
    decoder.decode(
        _build_shared_memory_v2_buffer(
            tick=1005.0,
            velocity_x_mps=-1.0,
            velocity_z_mps=0.0,
            speed_mps=1.0,
            absolute_x_m=999.0,
            absolute_z_m=1999.8,
        ),
        mono_time_s=11.0,
    )
    frame3 = decoder.decode(
        _build_shared_memory_v2_buffer(
            tick=1010.0,
            velocity_x_mps=-1.0,
            velocity_z_mps=0.0,
            speed_mps=1.0,
            absolute_x_m=998.8,
            absolute_z_m=1999.76,
        ),
        mono_time_s=12.0,
    )

    assert frame3.pose.world_z == pytest.approx(0.0, abs=1e-6)
    assert frame3.pose.yaw_rad == pytest.approx(0.0, abs=1e-6)
    assert decoder.last_state is not None
    assert decoder.last_state.heading_source == "absolute_position_hold"


def test_shared_memory_v2_decoder_resets_anchor_after_large_absolute_jump():
    decoder = SharedMemoryV2Decoder(
        SharedMemoryV2Config(
            absolute_x_offset=285,
            absolute_z_offset=301,
            absolute_value_format="f64",
            pose_frame_mode="anchored_local",
            absolute_heading_min_distance_m=0.25,
            absolute_discontinuity_distance_m=25.0,
        )
    )

    decoder.decode(
        _build_shared_memory_v2_buffer(
            velocity_x_mps=-4.0,
            velocity_z_mps=0.0,
            speed_mps=4.0,
            absolute_x_m=1000.0,
            absolute_z_m=2000.0,
        ),
        mono_time_s=10.0,
    )
    decoder.decode(
        _build_shared_memory_v2_buffer(
            tick=1005.0,
            velocity_x_mps=-4.0,
            velocity_z_mps=0.0,
            speed_mps=4.0,
            absolute_x_m=992.0,
            absolute_z_m=2000.0,
        ),
        mono_time_s=12.0,
    )
    jumped = decoder.decode(
        _build_shared_memory_v2_buffer(
            tick=1010.0,
            velocity_x_mps=0.0,
            velocity_z_mps=0.0,
            speed_mps=0.0,
            absolute_x_m=1300.0,
            absolute_z_m=2600.0,
        ),
        mono_time_s=13.0,
    )

    assert jumped.pose.world_x == pytest.approx(0.0)
    assert jumped.pose.world_z == pytest.approx(0.0)
    assert jumped.pose.yaw_rad == pytest.approx(0.0)
    assert decoder.last_state is not None
    assert decoder.last_state.pose_frame == "anchored_local_pending_heading"
    assert decoder.last_state.anchor_heading_locked is False
    assert decoder.last_state.discontinuity_detected is True
    assert decoder.last_state.anchor_reset_count == 1
    assert decoder.last_state.anchor_reset_reason == "absolute_position_jump"
    assert decoder.last_state.discontinuity_distance_m == pytest.approx(math.hypot(308.0, 600.0))


def test_shared_memory_v2_decoder_relocks_after_discontinuity_reset():
    decoder = SharedMemoryV2Decoder(
        SharedMemoryV2Config(
            absolute_x_offset=285,
            absolute_z_offset=301,
            absolute_value_format="f64",
            pose_frame_mode="anchored_local",
            absolute_heading_min_distance_m=0.25,
            absolute_discontinuity_distance_m=25.0,
        )
    )

    decoder.decode(
        _build_shared_memory_v2_buffer(
            velocity_x_mps=-4.0,
            velocity_z_mps=0.0,
            speed_mps=4.0,
            absolute_x_m=1000.0,
            absolute_z_m=2000.0,
        ),
        mono_time_s=10.0,
    )
    decoder.decode(
        _build_shared_memory_v2_buffer(
            tick=1005.0,
            velocity_x_mps=-4.0,
            velocity_z_mps=0.0,
            speed_mps=4.0,
            absolute_x_m=992.0,
            absolute_z_m=2000.0,
        ),
        mono_time_s=12.0,
    )
    decoder.decode(
        _build_shared_memory_v2_buffer(
            tick=1010.0,
            velocity_x_mps=0.0,
            velocity_z_mps=0.0,
            speed_mps=0.0,
            absolute_x_m=1300.0,
            absolute_z_m=2600.0,
        ),
        mono_time_s=13.0,
    )
    relocked = decoder.decode(
        _build_shared_memory_v2_buffer(
            tick=1015.0,
            velocity_x_mps=0.0,
            velocity_z_mps=-4.0,
            speed_mps=4.0,
            absolute_x_m=1300.0,
            absolute_z_m=2592.0,
        ),
        mono_time_s=15.0,
    )

    assert relocked.pose.world_x == pytest.approx(8.0)
    assert relocked.pose.world_z == pytest.approx(0.0, abs=1e-6)
    assert relocked.pose.yaw_rad == pytest.approx(0.0, abs=1e-6)
    assert decoder.last_state is not None
    assert decoder.last_state.pose_frame == "anchored_local"
    assert decoder.last_state.heading_source == "absolute_position_delta"
    assert decoder.last_state.anchor_heading_locked is True
    assert decoder.last_state.discontinuity_detected is False
    assert decoder.last_state.anchor_reset_count == 1


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
