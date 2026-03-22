# Implementation Status

## 2026-03-22 실제 검증 스냅샷

### 이번 세션에서 새로 확인된 것
- 실제 ATS world graph 경로를 하나로 고정했다.
  - 선택한 source/toolchain: `truckermudgeon/maps` 공개 `usa-graph-demo.json`
  - 선택 이유: 지금 이 머신에서 바로 재현 가능하고, 별도 exporter 설치 없이 ATS 실좌표와 비교할 수 있는 가장 작은 실경로라서
- `src/ats_cinepilot/map/projections.py`에 ATS Lambert Conformal Conic 변환을 추가했다.
  - `ats_coords_to_wgs84`
  - `wgs84_to_ats_coords`
- `trucksim_maps` adapter가 `demoGraph` + `demoNodes` 형식을 직접 읽는다.
  - `demoNodes`의 `lon/lat`를 ATS absolute `x/z`로 역변환해서 internal graph cache로 넣는다.
- `scripts/export_map.py`가 live shared-memory absolute pose를 중심으로 공개 demo graph를 잘라서 internal cache로 저장한다.
  - 현재 검증에 쓴 캐시: `data/maps/cache/ats_usa_region_real_graph_8km.json`
  - 현재 메타데이터:
    - `source_node_count = 175565`
    - `source_edge_count = 375577`
    - `cropped_node_count = 2015`
    - `cropped_edge_count = 4092`
    - `alignment_mode = ats_absolute_identity`
- matcher/app/recorder/startup summary가 graph source / alignment / nearest-edge distance / candidate count를 실제로 남긴다.
- raw live capture 하나를 두 pose frame으로 다시 decode해서 toy graph와 real graph를 같은 움직임으로 A/B 비교할 수 있게 했다.
  - `scripts/convert_shared_memory_v2_capture_to_replay.py`
  - `scripts/record_telemetry_replay.py`
  - `scripts/summarize_shadow_log.py`

### 현재 채택한 실좌표 계약
- `285:f64` -> `world_x`
- `293:f64` -> `world_y`
- `301:f64` -> `world_z`

이 계약은 이제 toy graph bring-up뿐 아니라 real graph identity alignment에서도 실제로 썼다.

## 구현돼 있고 실제로 돌아간 것

- replay telemetry source
- HTTP JSON telemetry source
- `shared_memory_v2` telemetry source
- absolute pose decode
- discontinuity detection + anchor reset
- raw capture / replay conversion / log summary tooling
- toy graph shadow mode
- real graph cache export from public `truckermudgeon/maps` demo graph
- ATS absolute pose -> real graph `ats_absolute_identity` alignment
- live shared-memory real-graph probe
- ATS-backed real-graph shadow run

## 현재 선택된 real graph 경로

- source/toolchain: `truckermudgeon/maps` 공개 `usa-graph-demo.json`
- internal adapter: `src/ats_cinepilot/map/adapters/trucksim_maps.py`
- export command:

```powershell
.\.venv\Scripts\python scripts\export_map.py --source trucksim-demo --input https://truckermudgeon.github.io/usa-graph-demo.json --output data\maps\cache\ats_usa_region_real_graph_8km.json --center-from-config configs\live_probe_moza_shared_memory.yaml --crop-radius-m 8000 --compact
```

- runtime config:
  - toy graph: `configs/live_probe_ats_toy_graph.yaml`
  - real graph: `configs/live_probe_ats_real_graph.yaml`

## real graph 정렬 전략

- graph source가 `lon/lat`로만 나오므로 adapter에서 다시 ATS absolute `x/z`로 역투영한다.
- 그래서 현재 선택한 정렬은 별도 magic constant 없이 `ats_absolute_identity`다.
  - scale: `1.0`
  - axis: ATS `world_x -> graph x`, ATS `world_z -> graph z`
  - offset: `0`
  - `world_y`는 현재 2D matcher에만선 안 쓴다.
- 이 선택은 “정밀 lane graph라서 완벽하다”는 뜻이 아니라, 현재 공개 artifact와 현재 absolute pose 계약이 같은 좌표계에 있다는 최소한의 계약이다.

## 검증 결과

### live probe

```powershell
.\.venv\Scripts\python scripts\inspect_telemetry.py --config configs\live_probe_ats_real_graph.yaml --frames 3
```

실제 결과:
- `SCSTelemetrySharedv2_ats` visible
- decode 성공
- `pose_source=authoritative_absolute`
- `pose_frame=world_absolute`
- absolute world pose와 update token 변화 확인

### 같은 raw capture로 한 A/B 비교

straight/light-turn capture를 같은 원본 raw shared-memory dump에서 두 번 decode해서 비교했다.

- toy graph (`anchored_local_toy_graph`)
  - `steps=150`
  - `safety={NONE: 88, MATCH_LOST: 62}`
  - `first_MATCH_LOST=89`
  - `match=[0.576, 1.000]`
  - `route=[0.468, 0.700]`
  - `cte_max=32.544`
  - `near=[0.000, 32.544]`
  - `cand=[1, 2]`
- real graph (`ats_absolute_identity`)
  - `steps=150`
  - `safety={MATCH_LOST: 150}`
  - `first_MATCH_LOST=1`
  - `match=[0.876, 0.951]`
  - `route=[0.419, 0.480]`
  - `cte_max=13.910`
  - `near=[6.187, 13.646]`
  - `cand=[2, 6]`

turn-heavy capture A/B:

- toy graph (`anchored_local_toy_graph`)
  - `steps=200`
  - `safety={NONE: 23, MATCH_LOST: 177}`
  - `first_MATCH_LOST=24`
  - `match=[0.000, 1.000]`
  - `route=[0.000, 0.700]`
  - `cte_max=44.690`
  - `near=[0.000, 44.690]`
  - `cand=[0, 1]`
  - `graph_failures={None: 95, no_nearby_edge: 105}`
- real graph (`ats_absolute_identity`)
  - `steps=200`
  - `safety={MATCH_LOST: 165, ROUTE_CONFIDENCE_LOW: 35}`
  - `first_MATCH_LOST=1`
  - `match=[0.822, 1.000]`
  - `route=[0.329, 0.499]`
  - `cte_max=9.680`
  - `near=[0.025, 9.680]`
  - `cand=[14, 23]`
  - `graph_failures={None: 200}`

해석:
- real graph가 turn-heavy에서도 **coverage 자체는 유지**했다.
  - toy graph처럼 `no_nearby_edge`가 쏟아지지 않았다.
  - nearest-edge distance와 cross-track error도 훨씬 낮았다.
- 그런데 공개 demo graph가 lane-accurate polyline graph가 아니라서 route confidence가 계속 낮고, safety gate를 통과할 만큼 정밀하지 않았다.

### 추가 live real-graph run

2026-03-22에 ATS 실주행 20초 샘플을 `world_absolute + ats_absolute_identity + real graph`로 직접 돌렸다.

- `steps=200`
- `safety={MATCH_LOST: 95, ROUTE_CONFIDENCE_LOW: 105}`
- `first_MATCH_LOST=1`
- `match=[0.951, 1.000]`
- `route=[0.404, 0.500]`
- `cte_max=3.301`
- `near=[0.005, 3.301]`
- `cand=[8, 21]`
- `heading_sources={velocity_direction: 1, absolute_position_delta: 182, absolute_position_hold: 17}`
- `graph_failures={None: 200}`

해석:
- absolute pose와 identity alignment 덕분에 real graph coverage는 실제 live run에서도 끊기지 않았다.
- 하지만 route confidence가 0.5 아래에 묶여서, 현재 safety gate 기준으론 “meaningful route following”까지는 못 갔다.

## 솔직한 현재 상태

이 저장소는 이제 아래까지는 실제로 검증됐다.

- replay shadow mode
- ATS-backed shared-memory telemetry ingest
- authoritative absolute position decode
- discontinuity reset
- toy graph bring-up
- real graph cache export
- ATS absolute pose와 real graph의 global identity alignment
- live real-graph shadow sample

하지만 아직 아래는 검증 주장 금지다.

- authoritative direct yaw field
- lane-accurate real ATS road graph alignment
- route-confidence가 충분한 real-graph shadow mode
- HUD calibration 실사용
- control sink write
- Active Mode

## 현재 가장 큰 병목

지금 dominant bottleneck은 heading semantics보다 **graph fidelity**다.

- `285/293/301` absolute pose 계약은 real graph와 붙여도 일관되게 nearby edge를 찾는다.
- turn-heavy에서도 coverage failure보다 route-confidence failure가 먼저 보인다.
- 공개 `usa-graph-demo.json`은 straight edge 중심의 coarse graph라서 lane/path 수준의 matching 품질이 안 나온다.

즉, 다음 단계는:
1. 더 정밀한 ATS road geometry exporter를 확보하거나
2. 최소 한 지역이라도 polyline/lane 수준 실그래프를 연결하고
3. 그 뒤에야 yaw field와 matcher 임계값의 실제 병목을 다시 분리하는 거다.

## 코드상 존재하지만 아직 실환경 미검증인 것

- authoritative direct yaw field (`309:f32`, `325:f32` 모두 아직 미채택)
- authoritative paused / world-state field
- authoritative game tick
- HUD preset 실제 캘리브레이션
- `scscontroller` 기반 control sink
- Active Mode
