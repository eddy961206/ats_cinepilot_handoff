# Shared Memory V2 Design Note

## 목적

ATS 1.58에서 `SCSTelemetrySharedv2_ats`를 앱 loop 안으로 안정적으로 넣고, 그 absolute pose를 실제 ATS graph 후보와 비교할 때 어떤 계약을 쓰는지 정리한 문서다.

이번 문서는 coarse public graph뿐 아니라, 이번 세션에서 선택한 **dense local ATS road GeoJSON path**까지 포함한다.

## 선택한 계약

- producer plugin: `atssharedplugin64v2.dll`
- selected mapping name: `SCSTelemetrySharedv2_ats`
- observed mapping size: `4096` bytes
- guard:
  - `raw[1:4] == b"ats"`
  - buffer 길이 `>= 768`

## 현재 채택한 offset

- `44:f32` -> `state_code` 후보
- `285:f64` -> `world_x`
- `293:f64` -> `world_y`
- `301:f64` -> `world_z`
- `333:f32` -> `velocity_x_mps`
- `357:f32` -> `velocity_z_mps`
- `445:f32` -> `speed_mps`
- `449:f32` -> `engine_rpm`
- `453:u32` -> `gear`
- `457:u32` -> `displayed_gear`
- `461:f32` -> `throttle`
- `507:f32` -> `speed_limit_kph` 후보
- `544:f32` -> `route_distance_km` 후보
- `548:f32` -> `route_time_min` 후보

## absolute pose 현재 결론

현재 authoritative absolute pose 계약은 그대로 유지한다.

- `285:f64` -> `world_x`
- `293:f64` -> `world_y`
- `301:f64` -> `world_z`

이 계약은 coarse public graph와 dense local geojson graph 둘 다에서 동일하게 썼다.

## yaw / heading 현재 결론

authoritative direct yaw offset은 아직 채택하지 않았다.

조사 후보:
- `309:f32`
- `325:f32`

현재 runtime heading 전략:
1. `absolute_position_delta`
2. `absolute_position_hold`
3. 없으면 `velocity_direction`

## discontinuity / reset 전략

absolute world position jump가 충분히 크면 stale anchor를 유지하지 않는다.

현재 전략:
1. 연속 두 absolute sample 사이 거리 계산
2. 거리가 `absolute_discontinuity_distance_m` 이상이면 discontinuity 판정
3. anchor / held heading / heading reference를 reset
4. 상태를 `anchored_local_pending_heading`으로 되돌림

## graph alignment

### coarse public baseline

- config: `configs/live_probe_ats_real_graph.yaml`
- source/toolchain: `truckermudgeon/maps` 공개 `usa-graph-demo.json`
- adapter: `src/ats_cinepilot/map/adapters/trucksim_maps.py`
- cache: `data/maps/cache/ats_usa_region_real_graph_8km.json`

### dense local selected path

- config: `configs/live_probe_ats_dense_local_graph.yaml`
- source/toolchain: 로컬 ATS install + `_ext/trucksim_maps_repo`
- export script: `scripts/export_local_dense_graph.py`
- selected export mode: focused ATS road GeoJSON
- cache: `data/maps/cache/ats_usa_region_dense_local_geojson_8km.json`

### 정렬 전략

현재 두 real-graph path 모두 `ats_absolute_identity`를 쓴다.

- axis:
  - ATS `world_x -> graph x`
  - ATS `world_z -> graph z`
- scale: `1.0`
- offset: `0`
- `world_y`는 현재 2D matcher에서 미사용

## dense local geojson path 메모

- `trucksim_maps` `map` generator는 focused region의 road GeoJSON을 준다.
- adapter는 road polyline을 internal graph edge로 변환한다.
- 기본 selected path는 forward-only edge다.
- `--synthetic-reverse-edges`는 실험용 옵션으로만 남겨뒀다.
  - 이유: reverse edge를 기본값으로 두면 ramp / one-way / branch semantics 검증이 오염돼서, dense graph가 정말 방향 정보를 담고 있는지 판단할 수 없었다.
  - 이번 세션 재검증에서도 reverse edge를 빼자 straight/light-turn에서 `heading_error≈π`가 다시 드러났고, turn-heavy에서는 route confidence가 오히려 높아졌다.

즉 현재 selected path는 **graph-side direction semantics를 솔직하게 드러내는 forward-only 계약**이다.

## dense local export 결과

command:

```powershell
.\.venv\Scripts\python scripts\export_local_dense_graph.py --config configs\live_probe_ats_real_graph.yaml --config configs\profiles\replay_ab_straight_light_turn.yaml --parser-output-dir "data\maps\trucksim_parser\ats_local" --geojson-output-dir "data\maps\trucksim_geojson\ats_local_region" --output-cache "data\maps\cache\ats_usa_region_dense_local_geojson_8km.json" --radius-m 8000
```

result:
- `node_count = 2143`
- `edge_count = 2156`
- `synthetic_reverse_edges = false`

## A/B 결과

### straight/light-turn

- coarse public replay
  - `steps=150`
  - `safety={MATCH_LOST: 150}`
  - `route=[0.419, 0.480]`
  - `cte_max=13.910`
- dense local geojson replay
  - same ATS-backed input
  - `steps=150`
  - `safety={MATCH_LOST: 150}`
  - `route=[0.447, 0.622]`
  - `cte_max=8.651`
  - `match=[0.617, 0.901]`

### turn-heavy

- coarse public replay
  - `steps=200`
  - `safety={MATCH_LOST: 165, ROUTE_CONFIDENCE_LOW: 35}`
  - `first_ROUTE_CONFIDENCE_LOW=80`
  - `route=[0.329, 0.499]`
  - `cte_max=9.680`
- dense local geojson replay
  - same ATS-backed input
  - `steps=200`
  - `safety={MATCH_LOST: 181, NONE: 19}`
  - `route=[0.482, 0.689]`
  - `cte_max=17.318`
  - `match=[0.706, 0.996]`

## 현재 결론

- `SCSTelemetrySharedv2_ats` direct reader는 실제로 동작한다.
- `285/293/301` absolute pose 계약은 유지한다.
- dense local geojson graph는 forward-only 계약에서 direction semantics bottleneck을 더 분명하게 드러냈다.
- straight/light-turn에서는 `heading≈π` mismatch가 남아 있고, turn-heavy에선 route confidence가 높아져도 `MATCH_LOST`가 많다.
- 그래서 다음 dominant bottleneck은 route source가 아니라 **graph-side direction semantics / heading handling**이다.
