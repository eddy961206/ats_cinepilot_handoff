from pathlib import Path

from scripts.export_local_dense_graph import _has_parser_output
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
