from ats_cinepilot.app import _build_vehicle_detector_config
from ats_cinepilot.ops.config import cfg_get, resolve_config


def test_cv_observer_dense_corridor_profile_resolves_expected_observer_contract():
    cfg = resolve_config(["configs/cv_observer_dense_corridor.yaml"])

    assert cfg_get(cfg, "telemetry.source") == "shared_memory_v2"
    assert cfg_get(cfg, "control.sink") == "noop"
    assert cfg_get(cfg, "cv.enabled") is True
    assert cfg_get(cfg, "cv.lane.enabled") is True
    assert cfg_get(cfg, "cv.vehicles.enabled") is True
    assert cfg_get(cfg, "cv.show_window") is True
    assert cfg_get(cfg, "cv.save_video") is True
    assert cfg_get(cfg, "map.source_name") == "curated_dense_local_corridor_graph"


def test_dense_active_cv_profile_extends_dense_demo_with_cv_guard():
    cfg = resolve_config(["configs/demo_active_dense_corridor_with_cv.yaml"])

    assert cfg_get(cfg, "control.sink") == "hybrid"
    assert cfg_get(cfg, "cv.enabled") is True
    assert cfg_get(cfg, "cv.guard.enabled") is True
    assert cfg_get(cfg, "cv.show_window") is False
    assert cfg_get(cfg, "logging.log_jsonl_path") == "data/logs/demo_active_dense_corridor_with_cv.jsonl"


def test_runtime_vehicle_detector_config_uses_pinned_cv_contract():
    cfg = resolve_config(["configs/demo_active_dense_corridor_with_cv.yaml"])

    detector_cfg = _build_vehicle_detector_config(cfg)

    assert detector_cfg.model_url == cfg_get(cfg, "cv.vehicles.model_url")
    assert detector_cfg.pbtxt_url == cfg_get(cfg, "cv.vehicles.pbtxt_url")
    assert detector_cfg.model_sha256 == cfg_get(cfg, "cv.vehicles.model_sha256")
    assert detector_cfg.pbtxt_sha256 == cfg_get(cfg, "cv.vehicles.pbtxt_sha256")
