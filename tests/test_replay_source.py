import json

from ats_cinepilot.bridge.scs_telemetry import ReplayTelemetrySource


def test_replay_source_reads_flat_frame_rows(tmp_path):
    path = tmp_path / "flat.jsonl"
    path.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "mono_time_s": 1.0,
                        "game_tick": 10,
                        "paused": False,
                        "speed_mps": 2.5,
                        "speed_limit_mps": 13.9,
                        "nav_distance_m": 120.0,
                        "pose": {"world_x": 10.0, "world_z": 20.0, "yaw_rad": 0.5},
                    }
                )
            ]
        ),
        encoding="utf-8",
    )

    source = ReplayTelemetrySource(path)
    source.connect()
    frame = source.read()

    assert frame is not None
    assert frame.game_tick == 10
    assert frame.pose.world_x == 10.0
    assert frame.pose.world_z == 20.0
    assert frame.pose.yaw_rad == 0.5


def test_replay_source_reads_recorder_rows_with_frame_wrapper(tmp_path):
    path = tmp_path / "wrapped.jsonl"
    path.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "frame": {
                            "mono_time_s": 2.0,
                            "game_tick": 11,
                            "paused": True,
                            "speed_mps": 0.0,
                            "speed_limit_mps": None,
                            "nav_distance_m": None,
                            "pose": {"world_x": -5.0, "world_z": 7.5, "yaw_rad": -0.25},
                        },
                        "status": {"graph_source": "live_log"},
                    }
                )
            ]
        ),
        encoding="utf-8",
    )

    source = ReplayTelemetrySource(path)
    source.connect()
    frame = source.read()

    assert frame is not None
    assert frame.game_tick == 11
    assert frame.paused is True
    assert frame.pose.world_x == -5.0
    assert frame.pose.world_z == 7.5
    assert frame.pose.yaw_rad == -0.25
