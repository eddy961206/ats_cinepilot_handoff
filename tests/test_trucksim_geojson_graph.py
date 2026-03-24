import json

import pytest

from ats_cinepilot.map.adapters.trucksim_maps import load_trucksim_graph
from ats_cinepilot.map.projections import ats_coords_to_wgs84


def test_load_trucksim_graph_supports_ats_geojson_roads_with_connectivity(tmp_path):
    a_lon, a_lat = ats_coords_to_wgs84(-100.0, 50.0)
    b_lon, b_lat = ats_coords_to_wgs84(0.0, 50.0)
    c_lon, c_lat = ats_coords_to_wgs84(80.0, 120.0)
    payload = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "id": "road_a",
                "properties": {
                    "type": "road",
                    "roadType": "local",
                    "startNodeUid": "1a",
                    "endNodeUid": "2b",
                    "dlcGuard": 0,
                },
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [a_lon, a_lat],
                        [b_lon, b_lat],
                    ],
                },
            },
            {
                "type": "Feature",
                "id": "road_b",
                "properties": {
                    "type": "road",
                    "roadType": "freeway",
                    "startNodeUid": "2b",
                    "endNodeUid": "3c",
                    "dlcGuard": 0,
                },
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [b_lon, b_lat],
                        [c_lon, c_lat],
                    ],
                },
            },
            {
                "type": "Feature",
                "id": "city_label",
                "properties": {"type": "city", "name": "Ignore Me"},
                "geometry": {"type": "Point", "coordinates": [b_lon, b_lat]},
            },
        ],
    }
    path = tmp_path / "ats.geojson"
    path.write_text(json.dumps(payload), encoding="utf-8")

    graph = load_trucksim_graph(path)

    assert graph.metadata["source_format"] == "trucksim_ats_geojson_roads"
    assert graph.metadata["source_feature_count"] == 3
    assert graph.metadata["road_feature_count"] == 2
    assert graph.metadata["synthetic_reverse_edge_count"] == 2
    assert graph.metadata["skipped_feature_count"] == 1
    assert set(graph.nodes) == {"1a", "2b", "3c"}
    assert graph.nodes["1a"].x == pytest.approx(-100.0, abs=1e-3)
    assert graph.nodes["1a"].z == pytest.approx(50.0, abs=1e-3)
    assert graph.nodes["3c"].x == pytest.approx(80.0, abs=1e-3)
    assert graph.nodes["3c"].z == pytest.approx(120.0, abs=1e-3)
    assert graph.edges["road_a__fwd"].start_node_id == "1a"
    assert graph.edges["road_a__fwd"].end_node_id == "2b"
    assert graph.edges["road_a__fwd"].road_class == "local"
    assert graph.edges["road_a__rev"].start_node_id == "2b"
    assert graph.edges["road_a__rev"].end_node_id == "1a"
    assert graph.edges["road_a__rev"].metadata["synthetic_reverse"] is True
    assert graph.edges["road_b__fwd"].road_class == "freeway"
    assert graph.edges["road_b__fwd"].points[-1][0] == pytest.approx(80.0, abs=1e-3)
    assert graph.edges["road_b__fwd"].points[-1][1] == pytest.approx(120.0, abs=1e-3)
    assert graph.edges["road_b__rev"].points[0][0] == pytest.approx(80.0, abs=1e-3)
    assert graph.edges["road_b__rev"].points[0][1] == pytest.approx(120.0, abs=1e-3)


def test_load_trucksim_graph_rejects_ats_geojson_without_connectable_roads(tmp_path):
    payload = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "id": "broken",
                "properties": {"type": "road", "roadType": "local"},
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [-120.0, 47.0],
                        [-119.0, 47.1],
                    ],
                },
            }
        ],
    }
    path = tmp_path / "broken.geojson"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="connectable ATS road features"):
        load_trucksim_graph(path)
