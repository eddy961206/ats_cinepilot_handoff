from ats_cinepilot.app import AutopilotApp
from ats_cinepilot.ops.config import cfg_get, resolve_config, validate_runtime_config


def test_replay_demo_profile_is_standalone_runnable():
    cfg = resolve_config(["configs/profiles/replay_demo.yaml"])

    assert cfg_get(cfg, "telemetry.source") == "replay"
    assert cfg_get(cfg, "map.cache_path") == "data/maps/cache/default_graph.json"
    assert validate_runtime_config(cfg, mode="shadow") == []

    app = AutopilotApp(cfg, mode="shadow")
    app.run_loop(steps=3)


def test_validate_runtime_config_reports_missing_replay_and_map_inputs():
    issues = validate_runtime_config(
        {
            "telemetry": {"source": "replay"},
            "logging": {"replay_path": "data/replays/does_not_exist.jsonl"},
        },
        mode="shadow",
    )

    assert any("logging.replay_path" in issue for issue in issues)
    assert any("map.cache_path" in issue for issue in issues)


def test_demo_active_corridor_profile_resolves_expected_demo_contract():
    cfg = resolve_config(["configs/demo_active_corridor.yaml"])

    assert cfg_get(cfg, "telemetry.source") == "shared_memory_v2"
    assert cfg_get(cfg, "control.sink") == "module"
    assert cfg_get(cfg, "map.source_name") == "toy_graph"
    assert cfg_get(cfg, "demo.enabled") is True
    assert cfg_get(cfg, "demo.approved_edge_ids") == ["ab"]
    assert cfg_get(cfg, "manual_override.flag_path") == "data/runtime/demo_override.flag"
