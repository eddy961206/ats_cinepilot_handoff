# Implementation Status

## 2026-03-23 실제 검증 스냅샷

### 이번 세션에서 새로 확인된 것

- 세션 시작 시점 기준 `main`은 PR #4까지였고, PR #5는 아직 open 상태였다.
- 그래서 이번 작업 베이스는 `main`이 아니라 `codex/real-ats-world-graph-alignment@06d9b67`였다.
- dense local ATS graph 경로를 하나로 고정했다.
  - selected toolchain: 로컬 ATS install + `_ext/trucksim_maps_repo`
  - selected export: `generator map --focusGameCoords --focusRadius --skipCoalescing`
  - selected adapter: `src/ats_cinepilot/map/adapters/trucksim_maps.py` 의 ATS road GeoJSON 경로
- dense local export script를 추가/정리했다.
  - file: `scripts/export_local_dense_graph.py`
  - contract:
    - parser output 재사용
    - focused ATS road GeoJSON 생성
    - internal graph cache로 변환
    - 기본값은 forward-only edge
    - `--synthetic-reverse-edges`는 실험용 옵션으로만 남김
- replay source가 recorder 로그의 `frame` wrapper도 직접 읽게 했다.
  - file: `src/ats_cinepilot/bridge/scs_telemetry.py`
  - 그래서 ATS-backed live log 하나를 graph A/B replay input으로 바로 쓸 수 있다.

## 현재 텔레메트리 계약

- mapping name: `SCSTelemetrySharedv2_ats`
- absolute pose:
  - `285:f64` -> `world_x`
  - `293:f64` -> `world_y`
  - `301:f64` -> `world_z`
- heading:
  - `absolute_position_delta`
  - `absolute_position_hold`
  - fallback `velocity_direction`
- discontinuity reset:
  - `absolute_discontinuity_distance_m = 25.0`

이 계약은 이번 세션에서도 유지했다. dense graph work 중 새로운 증거로 뒤집히지 않았다.

## 현재 선택된 그래프 경로

### toy baseline
- config: `configs/live_probe_ats_toy_graph.yaml`
- alignment: `anchored_local_toy_graph`

### coarse public real graph
- config: `configs/live_probe_ats_real_graph.yaml`
- cache: `data/maps/cache/ats_usa_region_real_graph_8km.json`
- source/toolchain: `truckermudgeon/maps` 공개 `usa-graph-demo.json`
- alignment: `ats_absolute_identity`

### dense local selected path
- config: `configs/live_probe_ats_dense_local_graph.yaml`
- cache: `data/maps/cache/ats_usa_region_dense_local_geojson_8km.json`
- source/toolchain: 로컬 ATS install + `_ext/trucksim_maps_repo`
- export mode: focused ATS road GeoJSON
- alignment: `ats_absolute_identity`

## dense local export 결과

command:

```powershell
.\.venv\Scripts\python scripts\export_local_dense_graph.py --config configs\live_probe_ats_real_graph.yaml --config configs\profiles\replay_ab_straight_light_turn.yaml --parser-output-dir "data\maps\trucksim_parser\ats_local" --geojson-output-dir "data\maps\trucksim_geojson\ats_local_region" --output-cache "data\maps\cache\ats_usa_region_dense_local_geojson_8km.json" --radius-m 8000
```

result metadata:
- `node_count = 2143`
- `edge_count = 2156`
- `graph_source = trucksim_local_geojson_region`
- `alignment_mode = ats_absolute_identity`
- `synthetic_reverse_edges = false`

현실 체크:
- local parser / geojson intermediate는 reproducible local artifact라 `.gitignore`로 제외했다.
- PR에는 runtime cache만 포함한다.

## A/B 비교

### straight/light-turn

- coarse public replay
  - input: ATS-backed `data/logs/ab_straight_real.jsonl`
  - `steps=150`
  - `safety={MATCH_LOST: 150}`
  - `first_MATCH_LOST=1`
  - `route=[0.419, 0.480]`
  - `cte_max=13.910`
- dense local geojson replay
  - same ATS-backed input
  - `steps=150`
  - `safety={MATCH_LOST: 150}`
  - `first_MATCH_LOST=1`
  - `route=[0.447, 0.622]`
  - `cte_max=8.651`
  - `match=[0.617, 0.901]`

### turn-heavy

- coarse public replay
  - input: ATS-backed `data/logs/ab_turn_real.jsonl`
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

### 해석

- synthetic reverse edge를 기본값에서 제거하자 straight/light-turn에서 `heading≈π` mismatch가 바로 드러났다.
- turn-heavy에서는 route confidence가 크게 좋아졌는데도 safety는 여전히 `MATCH_LOST`가 우세했다.
- 즉 dense local graph는 graph coverage를 넘어서서 direction semantics 문제를 드러내는 단계까지 왔지만, 아직 방향성/heading 평가가 충분히 맞지 않는다.

## 현재 가장 큰 병목

현재 dominant bottleneck은 **route source가 아니라 graph-side direction semantics / heading handling**이다.

근거:
- forward-only dense local geojson 경로에서 straight/light-turn이 `heading≈π` 때문에 바로 무너진다.
- turn-heavy에서는 route confidence가 높아져도 safety가 주로 `MATCH_LOST`에서 죽는다.
- reverse edge를 억지로 추가하면 straight는 나아지지만 direction semantics 검증 자체가 오염된다.
- 그래서 “route intent가 없어서 못 고른다”보다, “현재 graph edge 방향성과 heading 평가가 아직 정확하지 않다”에 더 가깝다.

## 다음 세션 권고

다음 세션은 **route source가 아니라 graph fidelity / direction semantics**에 집중해야 한다.

우선순위:
1. dense local geojson edge direction semantics 검토
2. matcher의 heading cost와 edge 방향 선택 로직 재검증
3. 그다음에도 turn-heavy가 약하면 yaw semantics 후보를 다시 비교

route source는 아직 이르다.

## 아직 미검증인 것

- authoritative direct yaw field
- paused / world-state authoritative field
- authoritative game tick
- trustworthy route source
- HUD calibration 실사용
- control sink write
- Active Mode
