# Shared Memory V2 Design Note

## 목적

ATS 1.58에서 `SCSTelemetrySharedv2_ats`를 앱 loop 안으로 안정적으로 넣고, 그 absolute pose를 toy graph가 아니라 **실제 ATS world graph 후보**와도 비교할 수 있게 하는 현재 지원 계약이다.

이 문서는 지금 로컬 머신에서 실제로 보인 mapping과, 이번 세션에서 연결한 real graph 경로를 기준으로만 적는다.

## 선택한 계약

- producer plugin: `atssharedplugin64v2.dll`
- selected mapping name: `SCSTelemetrySharedv2_ats`
- observed mapping size: `4096` bytes
- header guard:
  - `raw[1:4] == b"ats"`
  - buffer 길이는 최소 `768` bytes 이상

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

검증 근거:
- controlled capture에서 움직일 때 `285/301`이 smooth하게 변한다.
- `293`은 거의 고정이라 높이 축처럼 보인다.
- `285/301` 변화량 기반 speed가 `speed_mps`와 plausibly 맞는다.
- 이번 세션에선 이 값을 공개 ATS graph에 직접 붙여도 일관되게 nearby edge가 잡혔다.

## yaw / heading 현재 결론

authoritative direct yaw offset은 아직 채택하지 않았다.

조사한 후보:
- `309:f32`
- `325:f32`

현재 결론:
- `309:f32`
  - 가장 yaw-like하다.
  - 그래도 reverse / teleport / real-graph alignment까지 포함해 authoritative contract로 올릴 만큼 증거가 충분하지 않다.
- `325:f32`
  - steering input 또는 yaw-rate-like 거동에 더 가깝다.
  - direct yaw 계약으로는 현재 부적합하다.

그래서 runtime heading 전략은 여전히 아래다.

1. absolute world position이 있을 때 `absolute_position_delta`
2. delta가 너무 작으면 `absolute_position_hold`
3. absolute position이 없을 때만 `velocity_direction`

기본값:
- `absolute_heading_min_distance_m = 0.25`
- `absolute_discontinuity_distance_m = 25.0`

## discontinuity / reset 전략

absolute world position jump가 충분히 크면 stale anchor를 유지하지 않는다.

현재 전략:
1. 연속 두 absolute sample 사이 거리 계산
2. 거리가 `absolute_discontinuity_distance_m` 이상이면 discontinuity 판정
3. 아래 상태 reset
   - absolute anchor position
   - anchor heading
   - held absolute heading
   - heading reference point
4. 현재 absolute sample을 새 anchor 원점으로 삼음
5. runtime pose를 `anchored_local_pending_heading`으로 되돌림
6. 다음 valid movement delta가 생길 때까지 provisional 상태 유지

runtime / recorder 진단:
- `discontinuity_detected`
- `discontinuity_distance_m`
- `anchor_reset_count`
- `anchor_reset_reason`

현재 reset reason:
- `absolute_position_jump`

## real graph 연결에서 선택한 정렬

이번 세션에서 real graph 경로를 하나로 고정했다.

- selected map source/toolchain: `truckermudgeon/maps` 공개 `usa-graph-demo.json`
- adapter: `src/ats_cinepilot/map/adapters/trucksim_maps.py`
- runtime graph cache: `data/maps/cache/ats_usa_region_real_graph_8km.json`

정렬 전략:
- 공개 graph는 `lon/lat`를 준다.
- adapter가 `lon/lat -> ATS world_x/world_z`로 역투영한다.
- 그래서 현재 정렬은 별도 magic constant 없이 `ats_absolute_identity`다.

즉:
- axis direction/sign:
  - ATS `world_x` -> graph `x`
  - ATS `world_z` -> graph `z`
- scale:
  - `1.0`
- offset/origin:
  - `0`
- `world_y`:
  - 현재 2D matcher에는 미사용

이건 “그래프가 충분히 정밀하다”는 뜻이 아니라, **absolute pose 계약과 공개 graph artifact가 같은 수학적 좌표계에 올라간다**는 뜻이다.

## real graph validation 결과

### 1. live probe

```powershell
.\.venv\Scripts\python scripts\inspect_telemetry.py --config configs\live_probe_ats_real_graph.yaml --frames 3
```

실제 결과:
- mapping visible
- decode 성공
- `pose_source=authoritative_absolute`
- `pose_frame=world_absolute`

### 2. 같은 raw capture로 한 toy vs real A/B

straight/light-turn A/B:
- toy graph
  - `steps=150`
  - `safety={NONE: 88, MATCH_LOST: 62}`
  - `first_MATCH_LOST=89`
  - `cte_max=32.544`
  - `cand=[1, 2]`
- real graph
  - `steps=150`
  - `safety={MATCH_LOST: 150}`
  - `first_MATCH_LOST=1`
  - `cte_max=13.910`
  - `cand=[2, 6]`

turn-heavy A/B:
- toy graph
  - `steps=200`
  - `safety={NONE: 23, MATCH_LOST: 177}`
  - `graph_failures={None: 95, no_nearby_edge: 105}`
  - `cte_max=44.690`
  - `cand=[0, 1]`
- real graph
  - `steps=200`
  - `safety={MATCH_LOST: 165, ROUTE_CONFIDENCE_LOW: 35}`
  - `graph_failures={None: 200}`
  - `cte_max=9.680`
  - `cand=[14, 23]`

해석:
- real graph는 turn-heavy에서도 graph coverage를 유지했다.
- absolute pose 계약이 크게 틀렸다면 이런 연속 coverage가 나오기 어렵다.
- 남는 문제는 heading보다는 graph geometry와 route semantics 쪽이 더 커 보인다.

### 3. live ATS-backed real-graph shadow sample

2026-03-22 실제 ATS 주행 20초 샘플:
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
- real graph와의 spatial alignment 자체는 live loop에서도 유지됐다.
- 하지만 공개 demo graph가 coarse해서 route confidence가 계속 낮다.

## validation workflow

1. shared-memory probe

```powershell
.\.venv\Scripts\python scripts\inspect_telemetry.py --config configs\live_probe_ats_real_graph.yaml --frames 3
```

2. 공개 graph export

```powershell
.\.venv\Scripts\python scripts\export_map.py --source trucksim-demo --input https://truckermudgeon.github.io/usa-graph-demo.json --output data\maps\cache\ats_usa_region_real_graph_8km.json --center-from-config configs\live_probe_moza_shared_memory.yaml --crop-radius-m 8000 --compact
```

3. raw capture 수집

```powershell
.\.venv\Scripts\python scripts\capture_shared_memory_v2.py --config configs\live_probe_moza_shared_memory.yaml --seconds 15 --hz 10 --delay 10 --label straight_light_turn_ab
.\.venv\Scripts\python scripts\capture_shared_memory_v2.py --config configs\live_probe_moza_shared_memory.yaml --seconds 20 --hz 10 --delay 10 --label turn_heavy_ab
```

4. raw capture를 두 pose frame replay로 변환

```powershell
.\.venv\Scripts\python scripts\convert_shared_memory_v2_capture_to_replay.py --input data\captures\shared_memory_v2\<capture>.jsonl --output data\replays\<name>_anchor.jsonl --config configs\live_probe_moza_shared_memory.yaml --pose-frame-mode anchored_local
.\.venv\Scripts\python scripts\convert_shared_memory_v2_capture_to_replay.py --input data\captures\shared_memory_v2\<capture>.jsonl --output data\replays\<name>_world.jsonl --config configs\live_probe_moza_shared_memory.yaml --pose-frame-mode world_absolute
```

5. toy / real A/B run

```powershell
.\.venv\Scripts\ats-cinepilot run --config configs\live_probe_ats_toy_graph.yaml --config data\debug\<toy_override>.yaml --mode shadow --steps 150
.\.venv\Scripts\ats-cinepilot run --config configs\live_probe_ats_real_graph.yaml --config data\debug\<real_override>.yaml --mode shadow --steps 150
```

6. 결과 요약

```powershell
.\.venv\Scripts\python scripts\summarize_shadow_log.py --input data\logs\ab_straight_toy.jsonl --input data\logs\ab_straight_real.jsonl --input data\logs\ab_turn_toy.jsonl --input data\logs\ab_turn_real.jsonl --json data\debug\ab_summary.json
```

## failure modes

- `mapping missing`
  - ATS world state가 아니거나 plugin이 mapping을 아직 안 열었을 수 있음
- `unsupported layout`
  - 같은 이름을 써도 offset이 다른 다른 plugin/version일 수 있음
- `stale/non-updating`
  - mapping은 보이지만 update token이 안 바뀜
- `anchored_local_pending_heading`
  - absolute position은 읽혔지만 아직 heading lock 전
- `absolute_position_jump`
  - recover / teleport / 큰 재배치
- `graph coarse but aligned`
  - absolute pose와 graph 좌표계는 맞는데, public graph geometry가 너무 성겨서 route confidence가 낮음

## 현재 결론

- `SCSTelemetrySharedv2_ats` direct reader는 로컬에서 구현/검증됐다.
- `285/293/301` absolute pose 계약은 real graph identity alignment에서도 실제로 쓸 수 있다.
- 현재 dominant bottleneck은 yaw field보다 **graph fidelity**다.
- 다음 단계는 lane-accurate ATS graph를 하나라도 확보해서, 그때 다시 yaw semantics와 matcher threshold를 분리하는 거다.
