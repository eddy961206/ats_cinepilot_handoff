from pathlib import Path

from ats_cinepilot.ops.config import resolve_config
from scripts.export_local_dense_graph import _has_parser_output
from scripts.export_local_dense_graph import DEFAULT_OUTPUT_CACHE
from scripts.export_map import _graph_source_name


def test_graph_source_name_maps_local_geojson_source():
    assert _graph_source_name("trucksim-ats-geojson") == "trucksim_local_geojson_region"
    assert _graph_source_name("trucksim") == "trucksim_demo_graph_region"
    assert _graph_source_name("ts-map") == "ts-map"


def test_has_parser_output_requires_expected_files(tmp_path):
    path = Path(tmp_path)
    assert _has_parser_output(path) is False

    for name in (
        "usa-nodes.json",
        "usa-roads.json",
        "usa-prefabs.json",
        "usa-prefabDescriptions.json",
        "usa-roadLooks.json",
    ):
        (path / name).write_text("[]", encoding="utf-8")

    assert _has_parser_output(path) is True


def test_dense_local_runtime_config_uses_export_default_cache_path():
    cfg = resolve_config(["configs/live_probe_ats_dense_local_graph.yaml"])

    assert cfg["map"]["cache_path"] == DEFAULT_OUTPUT_CACHE
