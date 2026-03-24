# ATS CinePilot

ATS에서 **안전하게 bring-up 가능한 cinematic shadow autopilot**을 만드는 프로젝트 스캐폴드야.

핵심 방향은 이거다.

- 순수 화면 AI보다 **텔레메트리 + 도로 그래프 + HUD 경로 힌트 + 규칙 기반 제어기**를 먼저 굳힌다.
- 첫 목표는 flashy한 Active Mode가 아니라 **실제 live telemetry ingest + 안정적인 Shadow Mode**다.
- MOZA R3는 v1에서 **수동 takeover 장치**다.
- control path, HUD 일반화, Active Mode는 telemetry semantics와 graph quality가 충분히 올라온 뒤에만 간다.

## 지금 실제로 확인된 것

- replay shadow mode 동작
- editable install / pytest / ruff 통과
- `SCSTelemetrySharedv2_ats` live mapping decode 성공
- authoritative absolute pose 계약 일부 확인
  - `285:f64` -> `world_x`
  - `293:f64` -> `world_y`
  - `301:f64` -> `world_z`
- ATS-backed Shadow Mode bring-up 성공
- discontinuity detection + anchor reset 동작
- coarse public real graph path 연결
  - source/toolchain: `truckermudgeon/maps` 공개 `usa-graph-demo.json`
  - cache: `data/maps/cache/ats_usa_region_real_graph_8km.json`
- dense local real graph path 연결
  - source/toolchain: 로컬 ATS 설치본 + `_ext/trucksim_maps_repo` `map --focusGameCoords --focusRadius --skipCoalescing`
  - export script: `scripts/export_local_dense_graph.py`
  - cache: `data/maps/cache/ats_usa_region_dense_local_geojson_8km.json`
  - geometry: ATS road GeoJSON polyline
  - note: `--synthetic-reverse-edges`는 실험용으로만 남겨두고 기본 selected path에서는 비활성화했다.

## 아직 확인 안 된 것

- authoritative direct yaw field
- lane-accurate ATS regional graph
- trustworthy route source
- HUD calibration 실사용
- `scs-sdk-controller` 기반 control write
- Active Mode

## 현재 결론

지금 dominant bottleneck은 **route source보다 graph-side direction semantics / heading handling**이야.

이번 세션에서 dense local ATS road GeoJSON path를 붙인 뒤:
- synthetic reverse edge를 기본값에서 빼자 straight/light-turn에서 `heading≈π` mismatch가 다시 드러났고
- turn-heavy에서는 route confidence가 오히려 더 높아졌지만
- safety는 여전히 주로 `MATCH_LOST`에서 죽었다

즉 지금은 route source를 붙일 타이밍이 아니라, **dense local graph의 direction semantics와 heading/matcher 동작을 더 손봐야 할 단계**다.

## 현재 선택된 live telemetry 경로

- plugin DLL: `atssharedplugin64v2.dll`
- mapping name: `SCSTelemetrySharedv2_ats`
- config: `configs/live_probe_moza_shared_memory.yaml`
- design note: `docs/SHARED_MEMORY_V2_DESIGN.md`

reader는 현재 아래를 쓴다.

- absolute position: `285/293/301`
- heading: `absolute_position_delta` + `absolute_position_hold`
- discontinuity reset: `absolute_discontinuity_distance_m = 25.0`

`309:f32`, `325:f32`는 direct yaw 후보지만 아직 채택하지 않았다.

## 그래프 경로

### coarse baseline
- config: `configs/live_probe_ats_real_graph.yaml`
- cache: `data/maps/cache/ats_usa_region_real_graph_8km.json`
- source/toolchain: `truckermudgeon/maps` 공개 `usa-graph-demo.json`
- alignment: `ats_absolute_identity`

### dense local selected path
- config: `configs/live_probe_ats_dense_local_graph.yaml`
- cache: `data/maps/cache/ats_usa_region_dense_local_geojson_8km.json`
- source/toolchain: 로컬 ATS 설치본 + `_ext/trucksim_maps_repo` `map --focusGameCoords --focusRadius --skipCoalescing`
- alignment: `ats_absolute_identity`

## dense local export 빠른 경로

전제:
- ATS 설치 경로: `D:\Steam\steamapps\common\American Truck Simulator`
- local toolchain: `C:\workspaces\python_workspace\_ext\trucksim_maps_repo`
- Windows Build Tools 필요

한 번만 준비:

```powershell
winget install --id Microsoft.VisualStudio.2022.BuildTools --exact --accept-package-agreements --accept-source-agreements --override "--wait --quiet --norestart --nocache --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended"
cd C:\workspaces\python_workspace\_ext\trucksim_maps_repo
npm install
```

주의:
- 이 repo에선 `npm install` 마지막 symlink postinstall이 Windows 권한 때문에 `EPERM`으로 죽을 수 있다.
- 그래도 `cityhash.node`, `gdeflate.node`, `tsx`가 이미 생겼으면 local export는 가능하다.
- export script는 parser output을 재사용해서 ATS road GeoJSON을 뽑는다.

export:

```powershell
.\.venv\Scripts\python scripts\export_local_dense_graph.py --config configs\live_probe_ats_real_graph.yaml --config configs\profiles\replay_ab_straight_light_turn.yaml --parser-output-dir "data\maps\trucksim_parser\ats_local" --geojson-output-dir "data\maps\trucksim_geojson\ats_local_region" --output-cache "data\maps\cache\ats_usa_region_dense_local_geojson_8km.json" --radius-m 8000
```

현재 export 결과:
- `node_count = 2143`
- `edge_count = 2156`

실험용 reverse edge를 넣고 싶으면 아래처럼 명시적으로 켜야 한다.

```powershell
.\.venv\Scripts\python scripts\export_local_dense_graph.py --config configs\live_probe_ats_real_graph.yaml --config configs\profiles\replay_ab_straight_light_turn.yaml --parser-output-dir "data\maps\trucksim_parser\ats_local" --geojson-output-dir "data\maps\trucksim_geojson\ats_local_region" --output-cache "data\maps\cache\ats_usa_region_dense_local_geojson_8km.json" --radius-m 8000 --synthetic-reverse-edges
```

## A/B 비교 결과

### straight/light-turn
- coarse real graph replay
  - `safety={MATCH_LOST: 150}`
  - `first_MATCH_LOST=1`
  - `route=[0.419, 0.480]`
  - `cte_max=13.910`
- dense local geojson replay
  - `safety={MATCH_LOST: 150}`
  - `first_MATCH_LOST=1`
  - `route=[0.447, 0.622]`
  - `cte_max=8.651`
  - `match=[0.617, 0.901]`

### turn-heavy
- coarse real graph replay
  - `safety={MATCH_LOST: 165, ROUTE_CONFIDENCE_LOW: 35}`
  - `first_ROUTE_CONFIDENCE_LOW=80`
  - `route=[0.329, 0.499]`
  - `cte_max=9.680`
- dense local geojson replay
  - `safety={MATCH_LOST: 181, NONE: 19}`
  - `route=[0.482, 0.689]`
  - `cte_max=17.318`
  - `match=[0.706, 0.996]`

해석:
- reverse edge를 기본값에서 빼자 straight/light-turn은 즉시 `heading≈π` 문제를 드러냈다.
- turn-heavy에서는 route confidence가 크게 좋아졌는데도 `MATCH_LOST`가 남았다.
- 즉 지금 병목은 route source보다 graph-side direction semantics / heading evaluation 쪽이다.
- 그래서 다음 세션은 route source가 아니라 graph-side direction semantics / heading handling이 맞다.

## 추천 작업 순서

1. `docs/CODEX_HANDOFF.md` 먼저 읽기
2. `.\scripts\setup_venv.ps1`
3. `ats-cinepilot check-config --config configs/profiles/replay_demo.yaml`
4. `ats-cinepilot run --config configs/profiles/replay_demo.yaml --mode shadow --steps 300`
5. `ats-cinepilot check-config --config configs/live_probe_ats_dense_local_graph.yaml`
6. `python scripts/inspect_telemetry.py --config configs/live_probe_ats_dense_local_graph.yaml --frames 3`
7. 필요하면 `python scripts/export_local_dense_graph.py ...`
8. `ats-cinepilot run --config configs/live_probe_ats_dense_local_graph.yaml --mode shadow --steps 300`
9. 그다음에도 품질이 안 오르면 route source로 가지 말고 direction semantics부터 다시 파기

## 문서 맵

- `docs/CODEX_HANDOFF.md`
- `docs/ARCHITECTURE.md`
- `docs/IMPLEMENTATION_STATUS.md`
- `docs/LOCAL_SETUP.md`
- `docs/PLUGIN_OPTIONS.md`
- `docs/SHARED_MEMORY_V2_DESIGN.md`
- `docs/RUNBOOK.md`
- `docs/SAFETY.md`
