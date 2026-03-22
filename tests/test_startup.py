from ats_cinepilot.ops.startup import build_startup_summary, validate_startup_requirements


def test_build_startup_summary_lists_runtime_choices():
    cfg = {
        "telemetry": {"source": "shared_memory_v2"},
        "control": {"sink": "noop"},
        "hud": {"preset_path": ""},
        "safety": {
            "telemetry_timeout_ms": 250,
            "min_map_match_confidence": 0.6,
            "min_route_confidence": 0.55,
        },
    }

    lines = build_startup_summary(cfg, mode="shadow")

    assert any("telemetry_source=shared_memory_v2" in line for line in lines)
    assert any("control_sink=noop" in line for line in lines)
    assert any("route_provider=none" in line for line in lines)
    assert any("hud_capture=disabled" in line for line in lines)


def test_validate_startup_requirements_blocks_probe_only_live_source():
    cfg = {
        "telemetry": {"source": "shared_memory_v2"},
        "control": {"sink": "noop"},
        "hud": {"preset_path": ""},
    }

    issues = validate_startup_requirements(cfg, mode="shadow")

    assert issues == []
