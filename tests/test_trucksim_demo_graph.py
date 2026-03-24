import json

import pytest

from ats_cinepilot.map.adapters.trucksim_maps import crop_graph_to_radius, load_trucksim_graph
from ats_cinepilot.map.projections import ats_coords_to_wgs84, wgs84_to_ats_coords


def test_ats_projection_round_trip_preserves_absolute_pose():
    x_m = -78915.685
    z_m = 23588.619

    lon, lat = ats_coords_to_wgs84(x_m, z_m)
    roundtrip_x_m, roundtrip_z_m = wgs84_to_ats_coords(lon, lat)

    assert roundtrip_x_m == pytest.approx(x_m, abs=1e-3)
    assert roundtrip_z_m == pytest.approx(z_m, abs=1e-3)


def test_load_trucksim_graph_supports_demo_graph_payload(tmp_path):
    a_lon, a_lat = ats_coords_to_wgs84(100.0, 200.0)
    b_lon, b_lat = ats_coords_to_wgs84(250.0, 200.0)
    payload = {
        "demoNodes": [
            ["a", [a_lon, a_lat]],
            ["b", [b_lon, b_lat]],
        ],
        "demoGraph": [
            ["a", {"f": [{"n": "b", "l": 150, "m": 5.0, "d": "f", "g": 31}]}],
            ["b", {}],
        ],
    }
    path = tmp_path / "usa-graph-demo.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    graph = load_trucksim_graph(path)

    assert graph.metadata["source_format"] == "trucksim_demo_graph"
    assert graph.nodes["a"].x == pytest.approx(100.0, abs=1e-3)
    assert graph.nodes["a"].z == pytest.approx(200.0, abs=1e-3)
    assert graph.nodes["b"].x == pytest.approx(250.0, abs=1e-3)
    assert graph.nodes["b"].z == pytest.approx(200.0, abs=1e-3)
    assert set(graph.edges) == {"a__b__f__0"}
    assert graph.edges["a__b__f__0"].points[0][0] == pytest.approx(100.0, abs=1e-3)
    assert graph.edges["a__b__f__0"].points[0][1] == pytest.approx(200.0, abs=1e-3)
    assert graph.edges["a__b__f__0"].points[1][0] == pytest.approx(250.0, abs=1e-3)
    assert graph.edges["a__b__f__0"].points[1][1] == pytest.approx(200.0, abs=1e-3)


def test_crop_graph_to_radius_keeps_only_local_region(tmp_path):
    a_lon, a_lat = ats_coords_to_wgs84(0.0, 0.0)
    b_lon, b_lat = ats_coords_to_wgs84(100.0, 0.0)
    c_lon, c_lat = ats_coords_to_wgs84(5000.0, 0.0)
    d_lon, d_lat = ats_coords_to_wgs84(5200.0, 0.0)
    payload = {
        "demoNodes": [
            ["a", [a_lon, a_lat]],
            ["b", [b_lon, b_lat]],
            ["c", [c_lon, c_lat]],
            ["d", [d_lon, d_lat]],
        ],
        "demoGraph": [
            ["a", {"f": [{"n": "b", "l": 100, "m": 4.0, "d": "f", "g": 31}]}],
            ["b", {}],
            ["c", {"f": [{"n": "d", "l": 200, "m": 8.0, "d": "f", "g": 31}]}],
            ["d", {}],
        ],
    }
    path = tmp_path / "usa-graph-demo.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    graph = load_trucksim_graph(path)
    cropped = crop_graph_to_radius(graph, center_x_m=0.0, center_z_m=0.0, radius_m=500.0)

    assert set(cropped.nodes) == {"a", "b"}
    assert set(cropped.edges) == {"a__b__f__0"}
    assert cropped.metadata["crop_center_x_m"] == 0.0
    assert cropped.metadata["crop_radius_m"] == 500.0
