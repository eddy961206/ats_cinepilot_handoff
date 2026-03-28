# Implementation Status

## 2026-03-28 실제 상태

### 이번 세션 base 상태

- 먼저 stacked lineage를 `main`으로 정리했다.
- consolidation PR:
  - `#10`
  - merge commit: `880cfa5e17da5a9aca8ad304ed350b35dee72021`
- 이번 feature 작업 base는 `main@880cfa5e17da5a9aca8ad304ed350b35dee72021`다.

## 지금 실제로 검증된 것

### telemetry / pose

- `SCSTelemetrySharedv2_ats` live ingest 동작
- absolute pose 계약 유지
  - `285:f64 -> world_x`
  - `293:f64 -> world_y`
  - `301:f64 -> world_z`
- discontinuity detection / anchor reset 동작

### control path

- `scs-sdk-controller` steering / blinker write는 실제로 보였다
- module throttle / brake는 아직 실사용 경로가 아니다
- keyboard `W/S`는 실제로 먹는다
- 현재 usable control path는 계속 `hybrid`
  - steering / blinkers: module sink
  - throttle / brake: keyboard sink

### constrained active demos

- straight constrained live active demo 존재
  - config: `configs/demo_active_corridor.yaml`
  - helper: `scripts/run_demo_active_corridor.ps1`
- gentle-curve constrained live active demo 존재
  - config: `configs/demo_active_gentle_curve.yaml`
  - helper: `scripts/run_demo_active_gentle_curve.ps1`
- curated denser-corridor constrained live active demo 존재
  - config: `configs/demo_active_dense_corridor.yaml`
  - helper: `scripts/run_demo_active_dense_corridor.ps1`

## 이번 세션에서 새로 실제로 된 것

### dense curated corridor 계약

- dense-local source graph를 그대로 general active에 쓰지 않았다
- 대신 one-chain curated corridor를 두고, run 시작 전에 live pose에 맞춰 runtime translation을 계산한다
- runner가 자동으로 하는 일:
  1. vehicle stop preflight
  2. live pose read
  3. current pose 기준 corridor trim + translation fit
  4. runtime corridor graph export
  5. shadow qualification
  6. bounded active demo

### 현재 dense corridor source chain

- base corridor source edge chain:
  - `62b676d1a430001__fwd`
  - `62b67708e830001__fwd`
- runtime에서는 현재 truck 위치에 따라 `dense_seg_03 -> dense_seg_04`처럼 trim된 sequence를 쓴다
- graph source는 계속 `curated_dense_local_corridor_graph`
- alignment는 계속 `ats_absolute_identity`
- telemetry pose frame은 `world_absolute`

## dense curated active demo 실제 결과

command:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_demo_active_dense_corridor.ps1 -ShadowSteps 12 -ActiveSteps 140 -ActiveCountdownSeconds 3
```

actual summary:

- `steps=152`
- `safety={MATCH_LOST: 31, ROUTE_CONFIDENCE_LOW: 4, DEMO_GUARD: 25, NONE: 92}`
- `first_MATCH_LOST=1`
- `first_ROUTE_CONFIDENCE_LOW=32`
- `match=[0.717, 1.000]`
- `route=[0.487, 0.700]`
- `cte_max=0.030`
- `near=[0.000, 0.030]`
- `cand=[1, 1]`
- `steering_abs_max=0.300`
- `non_trivial_steering_count=35`
- `throttle_command_count=31`
- `brake_command_count=121`
- `demo_guard_reasons={bootstrap: 31, arming: 16, speed_cap_exceeded: 13, armed: 92}`

해석:

- dense corridor에서도 real steering / throttle / brake가 같은 run 안에서 실제로 적용됐다
- review fix 이후에도 runtime fit이 `dense_seg_04` 단일 edge corridor로 trim된 상태에서 candidate count는 계속 `1`
- `cte_max=0.030`로 safety cage 안에 머문 구간이 충분히 있었다
- `safety=NONE`이 `92` step 유지돼서 demo milestone로는 성립한다
- 다만 longitudinal shaping이 여전히 거칠어서 `speed_cap_exceeded` brake assist가 많이 개입한다

## 현재 선택 계약

### straight demo

- graph: `toy_graph`
- alignment: `anchored_local_toy_graph`
- corridor: `ab`
- sink: `hybrid`

### gentle-curve demo

- graph: `toy_gentle_curve_graph`
- alignment: `anchored_local_toy_graph`
- corridor: `curve_ab`
- sink: `hybrid`
- speed cap: `3.0 m/s`

### dense curated demo

- graph: `curated_dense_local_corridor_graph`
- alignment: `ats_absolute_identity`
- contract base: `configs/corridors/demo_dense_curated_corridor.yaml`
- runtime overlay: `data/runtime/demo_dense_curated_corridor.runtime.yaml`
- runtime graph: `data/maps/cache/demo_dense_curated_corridor.runtime.json`
- sink: `hybrid`
- stop preflight: `scripts/ensure_demo_stop.py`
- fit helper: `scripts/fit_demo_dense_corridor.py`

## demo cage 조건

active control 허용 조건:

- live telemetry healthy
- `control.sink=hybrid`
- approved graph / alignment 일치
- approved edge sequence 일치
- travel direction = `forward`
- pose source = `authoritative_absolute`
- heading source = `absolute_position_delta | absolute_position_hold`
- preview path 존재
- match confidence floor 충족
- route confidence floor 충족
- cross-track error ceiling 충족
- heading error ceiling 충족
- nearest-edge distance ceiling 충족
- graph candidate count ceiling 충족
- speed cap 충족
- discontinuity 없음
- anchor locked
- manual override 없음

실패 시 동작:

- 즉시 neutralize
- keyboard key release
- `demo_guard_reason` 기록
- speed cap exceeded일 때만 brake-only assist 허용

## 현재 한계

- module longitudinal는 아직 실사용 계약이 아니다
- keyboard longitudinal는 ATS foreground focus가 필요하다
- dense demo corridor는 runtime fit된 one-chain corridor 하나뿐이다
- dense-local general active driving은 아직 아니다
- route-aware active는 아직 아니다
- complex intersection / broader route following은 아직 아니다

## 현재 결론

이번 milestone은 **첫 curated denser-corridor constrained live active demo**다.

정확한 의미:

- telemetry는 live다
- steering write path는 live module path로 적용됐다
- throttle / brake는 live hybrid path로 적용됐다
- translated dense corridor 위에서 real active steering이 실제로 걸렸다
- safety cage가 bootstrap / arming / armed / brake assist를 실제로 수행했다

아직 의미하지 않는 것:

- dense-local general active driving
- route-following autonomy
- complex intersection handling
- production-quality autopilot

## 다음 dominant bottleneck

지금 가장 큰 병목은 `route source`가 아니라 **curated corridor repeatability와 low-speed longitudinal shaping**이다.

더 좁게 말하면:

- dense curated corridor demo 자체는 성립했다
- 하지만 stop/start, bootstrap, speed-cap brake assist가 아직 demo 전용으로 많이 개입한다
- 다음 확장은 route-aware가 아니라 `slightly richer multi-edge curated corridor`가 맞다

## 다음 추천 작업

1. dense curated corridor demo를 같은 helper로 반복 재현
2. demo-only longitudinal shaping을 조금 더 다듬기
3. 그 다음에만 curated multi-edge corridor로 넓히기
4. route-aware demo는 그 다음에 판단
