# Implementation Status

## 2026-03-25 실제 상태

### 이번 세션 base 상태

- `main`은 아직 PR #5까지만 포함한다.
- PR #6, PR #7 내용은 `origin/codex/real-ats-world-graph-alignment` stacked lineage에 있다.
- 이번 세션 작업 베이스는 `codex/dense-graph-direction-semantics@1ed1e75` 위다.
- 즉 이번 세션은 updated `main` 기반이 아니라, graph-semantics stacked lineage 기반이다.

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
- 현재 dominant bottleneck은 여전히 route source가 아니라 dense local graph fidelity 쪽이다

### control path

- `scs-sdk-controller` DLL patched build를 ATS plugin dir에 실제 배치했다
  - callback context bug patch 반영
- module steering write는 실제로 보였다
  - operator visual confirmation 완료
- module left blinker write는 실제로 보였다
  - operator visual confirmation 완료
- module throttle / brake는 아직 실구동 실패
  - `aforward`
  - `aforward + activate`
  - `aforward + parkingbrake=false`
  - `aforward + drive`
  - 위 조합을 telemetry와 같이 찍었지만 속도 상승이 없었다
- keyboard `W/S` write는 실제로 먹는다
  - `W 5초` 전진 operator confirmation 완료
- 그래서 현재 선택된 demo sink는 `hybrid`
  - steering / blinkers: module sink
  - throttle / brake: keyboard sink

### constrained active demo

- `configs/demo_active_corridor.yaml` 존재
- strict demo cage 존재
- human-runnable helper 존재
  - `scripts/run_demo_active_corridor.ps1`
  - `scripts/demo_override_on.ps1`
  - `scripts/demo_override_off.ps1`
- live hybrid micro-probe 성공
  - 같은 프로세스에서 telemetry와 함께 검증
  - throttle 구간: `3.611 -> 13.777 m/s`
  - brake 구간: `15.340 -> 0.000 m/s`
- 첫 constrained live active demo attempt 성공
  - command: `scripts/run_demo_active_corridor.ps1 -ShadowSteps 20 -ActiveSteps 80 -ActiveCountdownSeconds 8`
  - active bootstrap 이후 speed가 `0.00 -> 2.54 m/s`
  - armed 이후 speed가 `2.51 -> 4.10 m/s`
  - speed cap exceeded 후 brake assist로 `5.34 -> 1.95 m/s`
  - 즉 throttle + brake는 실제 active loop 안에서 적용됐다
- 다만 chosen corridor가 직선 toy segment라 active run 중 steering command는 거의 0에 가까웠다
  - steering write path 자체는 module pulse로 따로 검증했다
  - “복잡한 코너까지 자동 조향이 검증됐다”는 뜻은 아니다

## 현재 선택 계약

### demo config

- file: `configs/demo_active_corridor.yaml`
- telemetry: `shared_memory_v2`
- graph: `toy_graph`
- alignment: `anchored_local_toy_graph`
- corridor: `ab`
- sink: `hybrid`

### demo cage 조건

active control 허용 조건:

- live telemetry healthy
- graph source = `toy_graph`
- alignment mode = `anchored_local_toy_graph`
- approved edge id = `ab`
- travel direction = `forward`
- direction confidence state = `confident`
- pose source = `authoritative_absolute`
- heading source = `absolute_position_delta | absolute_position_hold`
- match confidence >= `0.99`
- route confidence >= `0.69`
- cross-track error <= `0.20 m`
- heading error <= `6.0 deg`
- nearest-edge distance <= `0.20 m`
- graph candidate count <= `1`
- speed <= `4.0 m/s`
- discontinuity 없음
- manual override 없음

실패 시 동작:

- 즉시 neutralize
- `demo_guard_reason` 기록
- speed cap exceeded이면 brake-only assist 허용

## 현재 한계

- module throttle / brake는 아직 실사용 계약이 아니다
- keyboard longitudinal은 ATS 창 focus가 필요하다
- background child process에서 keyboard write가 흔들릴 수 있다
- direct yaw field는 아직 채택 안 했다
- dense local graph turn-heavy reliability는 아직 부족하다
- route-aware autonomy는 아직 아니다
- general Active Mode라고 부를 단계는 아니다

## 현재 결론

이번 milestone은 **첫 tightly constrained live active demo bring-up**이다.

정확한 의미:

- telemetry는 live다
- steering write path는 live module pulse로 확인됐다
- throttle / brake write path는 live hybrid probe와 active loop에서 확인됐다
- safety cage가 실제로 arm / disarm / brake assist를 했다

아직 의미하지 않는 것:

- 일반 도로 자율주행
- 복잡한 intersection handling
- full route following
- production-quality active autopilot

## 다음 dominant bottleneck

지금 가장 큰 병목은 control path 자체보다 **demo corridor/generalization 바깥의 graph semantics**다.

더 좁게 말하면:

- 이 constrained demo는 성립했다
- 하지만 toy corridor 밖으로 넓히려면 dense local graph와 route intent가 다시 병목이 된다

## 다음 추천 작업

1. 이 demo 경로를 human-run 절차로 한 번 더 재현
2. hybrid sink focus 요구사항을 운영 절차로 고정
3. 그 다음에만 corridor를 조금 넓히거나, route source를 아주 좁게 붙이기
4. module longitudinal 계약은 별도 트랙으로 계속 확인
