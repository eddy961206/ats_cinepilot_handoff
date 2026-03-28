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
    assert cfg_get(cfg, "control.sink") == "hybrid"
    assert cfg_get(cfg, "control.module_search_paths") == ["../_ext/scs-sdk-controller"]
    assert cfg_get(cfg, "map.source_name") == "toy_graph"
    assert cfg_get(cfg, "demo.enabled") is True
    assert cfg_get(cfg, "demo.approved_edge_ids") == ["ab"]
    assert cfg_get(cfg, "demo.min_progress_m") == 0.0
    assert cfg_get(cfg, "demo.allow_speed_cap_brake_assist") is True
    assert cfg_get(cfg, "manual_override.flag_path") == "data/runtime/demo_override.flag"


def test_demo_active_gentle_curve_profile_resolves_expected_demo_contract():
    cfg = resolve_config(["configs/demo_active_gentle_curve.yaml"])

    assert cfg_get(cfg, "telemetry.source") == "shared_memory_v2"
    assert cfg_get(cfg, "control.sink") == "hybrid"
    assert cfg_get(cfg, "map.cache_path") == "data/maps/cache/demo_gentle_curve_graph.json"
    assert cfg_get(cfg, "map.source_name") == "toy_gentle_curve_graph"
    assert cfg_get(cfg, "demo.enabled") is True
    assert cfg_get(cfg, "demo.corridor_name") == "toy_gentle_curve_low_speed"
    assert cfg_get(cfg, "demo.approved_edge_ids") == ["curve_ab"]
    assert cfg_get(cfg, "demo.max_speed_mps") == 3.0
    assert cfg_get(cfg, "truck.preferred_speed_cap_mps") == 3.0
    assert cfg_get(cfg, "control.keyboard.longitudinal_pwm_period_s") == 0.25
    assert cfg_get(cfg, "logging.log_jsonl_path") == "data/logs/demo_active_gentle_curve.jsonl"


def test_demo_active_dense_corridor_profile_resolves_expected_demo_contract():
    cfg = resolve_config(["configs/demo_active_dense_corridor.yaml"])

    assert cfg_get(cfg, "telemetry.source") == "shared_memory_v2"
    assert cfg_get(cfg, "control.sink") == "hybrid"
    assert cfg_get(cfg, "map.cache_path") == "data/maps/cache/demo_dense_curated_corridor_graph.json"
    assert cfg_get(cfg, "map.source_name") == "curated_dense_local_corridor_graph"
    assert cfg_get(cfg, "map.alignment_mode") == "ats_absolute_identity"
    assert cfg_get(cfg, "demo.enabled") is True
    assert cfg_get(cfg, "demo.contract_path") == "configs/corridors/demo_dense_curated_corridor.yaml"
    assert cfg_get(cfg, "demo.max_speed_mps") == 2.5
    assert cfg_get(cfg, "logging.log_jsonl_path") == "data/logs/demo_active_dense_corridor.jsonl"
