# Implementation Status

## 2026-03-26 실제 상태

### 이번 세션 base 상태

- `main`이 아니라 `codex/real-ats-world-graph-alignment@3443e94707d7f17c32cee488753627251393eab4`를 베이스로 썼다.
- 즉 이번 세션은 stale `main` 기반이 아니라 PR #6 / #7 / #8 lineage가 이미 들어있는 integration branch 기반이다.

## 지금 실제로 검증된 것

### telemetry / pose

- `SCSTelemetrySharedv2_ats` live ingest 동작
- absolute pose 계약 유지
  - `285:f64 -> world_x`
  - `293:f64 -> world_y`
  - `301:f64 -> world_z`
- discontinuity detection / anchor reset 동작

### shadow / graph

- replay shadow mode 동작
- ATS-backed shadow bring-up 동작
- toy graph / coarse real graph / dense local graph 경로 존재
- dense local graph matcher diagnostics / reverse-heading rescue / continuity gating 존재
- dense local graph는 아직 shadow generalization 병목을 완전히 해소하지 못했다

### control path

- `scs-sdk-controller` patched DLL을 ATS plugin dir에 실제 배치했다
- module steering write는 실제로 보였다
- module left blinker write는 실제로 보였다
- module throttle / brake는 아직 실사용 경로가 아니다
- keyboard `W/S` write는 실제로 먹는다
- 현재 usable demo sink는 `hybrid`
  - steering / blinkers: module sink
  - throttle / brake: keyboard sink

### constrained active demos

- straight constrained live active demo 존재
  - config: `configs/demo_active_corridor.yaml`
  - helper: `scripts/run_demo_active_corridor.ps1`
- gentle-curve constrained live active demo 존재
  - config: `configs/demo_active_gentle_curve.yaml`
  - helper: `scripts/run_demo_active_gentle_curve.ps1`
- gentle-curve demo는 keyboard longitudinal PWM을 사용한다
  - `control.keyboard.longitudinal_pwm_period_s=0.25`

## 이번 세션의 실제 gentle-curve 결과

### baseline

- straight corridor baseline은 유지됐다
- 기존 straight demo 계약은 그대로 남겨뒀다

### curved shadow qualification

- stationary shadow qualification은 통과했다
- 이후 live curved active에서 실제 closed-loop steering demand가 확인됐다

### curved active demo result

command:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_demo_active_gentle_curve.ps1 -ShadowSteps 25 -ActiveSteps 120 -ActiveCountdownSeconds 8
```

actual summary:

- `steps=145`
- `safety={NONE: 111, MATCH_LOST: 9, DEMO_GUARD: 24, ROUTE_CONFIDENCE_LOW: 1}`
- `first_MATCH_LOST=92`
- `match=[0.997, 1.000]`
- `route=[0.681, 0.700]`
- `cte_max=0.240`
- `cand=[1, 1]`
- `steering_abs_max=0.209`
- `non_trivial_steering_count=32`
- `throttle_command_count=126`
- `brake_command_count=18`
- `demo_guard_reasons={bootstrap: 91, heading_source_unapproved: 4, arming: 11, armed: 20, speed_cap_exceeded: 19}`

해석:

- 곡선 구간에서 steering이 실제로 0이 아니었다
- throttle / brake도 같은 run 안에서 실제로 적용됐다
- 즉 첫 gentle-curve constrained live active demo는 성립했다
- 다만 `speed_cap_exceeded`가 여전히 주요 disengage 원인이라, longitudinal shaping은 아직 거칠다

## 현재 선택 계약

### straight demo

- file: `configs/demo_active_corridor.yaml`
- telemetry: `shared_memory_v2`
- graph: `toy_graph`
- alignment: `anchored_local_toy_graph`
- corridor: `ab`
- sink: `hybrid`

### gentle-curve demo

- file: `configs/demo_active_gentle_curve.yaml`
- telemetry: `shared_memory_v2`
- graph: `toy_gentle_curve_graph`
- alignment: `anchored_local_toy_graph`
- corridor: `curve_ab`
- sink: `hybrid`
- speed cap: `3.0 m/s`
- keyboard longitudinal PWM: `0.25 s`

## demo cage 조건

active control 허용 조건:

- live telemetry healthy
- approved graph / alignment 일치
- approved edge id 일치
- travel direction = `forward`
- direction confidence state = `confident`
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
- `demo_guard_reason` 기록
- speed cap exceeded일 때만 brake-only assist 허용

## 현재 한계

- module longitudinal는 아직 실사용 계약이 아니다
- keyboard longitudinal은 ATS foreground focus가 필요하다
- keyboard longitudinal는 저속 curve demo에서 아직도 거칠다
- direct yaw field는 아직 채택 안 했다
- dense local graph active generalization은 아직 범위 밖이다
- route-aware autonomy는 아직 아니다
- general Active Mode라고 부를 단계는 아니다

## 현재 결론

이번 milestone은 **첫 straight demo 다음 단계인 첫 gentle-curve constrained live active demo**다.

정확한 의미:

- telemetry는 live다
- steering write path는 live module path로 적용됐다
- throttle / brake는 live hybrid path로 적용됐다
- 곡선 구간에서 의미 있는 non-zero steering이 실제로 발생했다
- safety cage가 arm / disarm / brake assist를 실제로 수행했다

아직 의미하지 않는 것:

- 일반 도로 active driving
- dense local graph active corridor
- route following
- complex intersection handling
- production-quality active autopilot

## 다음 dominant bottleneck

지금 가장 큰 병목은 steering sign보다 **demo longitudinal shaping과 corridor fidelity**다.

더 좁게 말하면:

- gentle-curve demo 자체는 성립했다
- 하지만 speed cap guard가 아직 빨리 걸린다
- 다음 확장은 route-following이 아니라 curated corridor fidelity / low-speed shaping 쪽이다

## 다음 추천 작업

1. gentle-curve demo를 human-run 절차로 반복 재현
2. keyboard longitudinal shaping을 demo 범위 안에서만 더 다듬기
3. 그 다음에만 curated denser corridor 1개로 확장 검토
4. module longitudinal는 별도 트랙으로 계속 isolate
