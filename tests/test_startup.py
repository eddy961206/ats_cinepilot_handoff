from ats_cinepilot.ops.startup import build_startup_summary, validate_startup_requirements


def test_build_startup_summary_lists_runtime_choices():
    cfg = {
        "telemetry": {"source": "shared_memory_v2"},
        "control": {"sink": "noop"},
        "hud": {"preset_path": ""},
        "map": {
            "source_name": "trucksim_demo_graph_region",
            "alignment_mode": "ats_absolute_identity",
        },
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
    assert any("graph_source=trucksim_demo_graph_region" in line for line in lines)
    assert any("alignment_mode=ats_absolute_identity" in line for line in lines)


def test_validate_startup_requirements_blocks_probe_only_live_source():
    cfg = {
        "telemetry": {"source": "shared_memory_v2"},
        "control": {"sink": "noop"},
        "hud": {"preset_path": ""},
    }

    issues = validate_startup_requirements(cfg, mode="shadow")

    assert issues == []


def test_build_startup_summary_lists_demo_cage_details():
    cfg = {
        "telemetry": {"source": "shared_memory_v2"},
        "control": {"sink": "module"},
        "hud": {"preset_path": ""},
        "map": {
            "source_name": "toy_graph",
            "alignment_mode": "anchored_local_toy_graph",
        },
        "manual_override": {"flag_path": "data/runtime/demo_override.flag"},
        "demo": {
            "enabled": True,
            "corridor_name": "toy_ab_demo",
            "approved_edge_ids": ["ab"],
            "max_speed_mps": 4.0,
        },
        "safety": {
            "telemetry_timeout_ms": 250,
            "min_map_match_confidence": 0.6,
            "min_route_confidence": 0.55,
        },
    }

    lines = build_startup_summary(cfg, mode="active")

    assert any("demo_enabled=yes corridor=toy_ab_demo" in line for line in lines)
    assert any("demo_edge_ids=ab" in line for line in lines)
    assert any("demo_max_speed_mps=4.0" in line for line in lines)
    assert any("manual_override_flag=data/runtime/demo_override.flag" in line for line in lines)


def test_validate_startup_requirements_rejects_incomplete_active_demo():
    cfg = {
        "telemetry": {"source": "shared_memory_v2"},
        "control": {"sink": "module", "module_name": "scscontroller", "class_name": "SCSController"},
        "map": {"source_name": "toy_graph", "alignment_mode": "anchored_local_toy_graph"},
        "demo": {
            "enabled": True,
            "corridor_name": "toy_ab_demo",
            "approved_graph_source": "toy_graph",
            "approved_alignment_mode": "anchored_local_toy_graph",
            "approved_edge_ids": [],
        },
    }

    issues = validate_startup_requirements(cfg, mode="active")

    assert "demo.approved_edge_ids must not be empty when demo.enabled=true." in issues


def test_validate_startup_requirements_rejects_keyboard_demo_sink():
    cfg = {
        "telemetry": {"source": "shared_memory_v2"},
        "control": {"sink": "keyboard"},
        "map": {"source_name": "toy_graph", "alignment_mode": "anchored_local_toy_graph"},
        "demo": {
            "enabled": True,
            "corridor_name": "toy_ab_demo",
            "approved_graph_source": "toy_graph",
            "approved_alignment_mode": "anchored_local_toy_graph",
            "approved_edge_ids": ["ab"],
        },
    }

    issues = validate_startup_requirements(cfg, mode="active")

    assert "demo active mode requires control.sink=hybrid." in issues


def test_validate_startup_requirements_allows_hybrid_demo_sink():
    cfg = {
        "telemetry": {"source": "shared_memory_v2"},
        "control": {"sink": "hybrid"},
        "map": {"source_name": "toy_graph", "alignment_mode": "anchored_local_toy_graph"},
        "demo": {
            "enabled": True,
            "corridor_name": "toy_ab_demo",
            "approved_graph_source": "toy_graph",
            "approved_alignment_mode": "anchored_local_toy_graph",
            "approved_edge_ids": ["ab"],
        },
    }

    issues = validate_startup_requirements(cfg, mode="active")

    assert issues == []


def test_validate_startup_requirements_rejects_non_hybrid_demo_sink():
    cfg = {
        "telemetry": {"source": "shared_memory_v2"},
        "control": {"sink": "keyboard"},
        "map": {"source_name": "toy_graph", "alignment_mode": "anchored_local_toy_graph"},
        "demo": {
            "enabled": True,
            "corridor_name": "toy_ab_demo",
            "approved_graph_source": "toy_graph",
            "approved_alignment_mode": "anchored_local_toy_graph",
            "approved_edge_ids": ["ab"],
        },
    }

    issues = validate_startup_requirements(cfg, mode="active")

    assert "demo active mode requires control.sink=hybrid." in issues


def test_validate_startup_requirements_rejects_demo_graph_contract_mismatch():
    cfg = {
        "telemetry": {"source": "shared_memory_v2"},
        "control": {"sink": "hybrid"},
        "map": {"source_name": "wrong_graph", "alignment_mode": "wrong_alignment"},
        "demo": {
            "enabled": True,
            "corridor_name": "toy_ab_demo",
            "approved_graph_source": "toy_graph",
            "approved_alignment_mode": "anchored_local_toy_graph",
            "approved_edge_ids": ["ab"],
        },
    }

    issues = validate_startup_requirements(cfg, mode="active")

    assert "demo.approved_graph_source must match map.source_name in active demo mode." in issues
    assert "demo.approved_alignment_mode must match map.alignment_mode in active demo mode." in issues
