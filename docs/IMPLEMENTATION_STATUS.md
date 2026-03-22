# Implementation Status

## 2026-03-22 실제 검증 스냅샷

### 이번 세션에서 새로 확인된 것
- `shared_memory_v2` reverse-engineering workflow를 정지, 좌회전, 우회전, 후진, teleport/recover 다섯 시나리오로 실제 반복 검증했다.
- raw capture는 `data/captures/shared_memory_v2/`에 남기고, 분석 결과는 JSON/CSV로 저장할 수 있게 했다.
- 현재 absolute pose 계약은 그대로 유지한다.
  - `285:f64` -> `world_x`
  - `293:f64` -> `world_y`
  - `301:f64` -> `world_z`
- `309:f32`, `325:f32`를 direct yaw 후보로 비교했다.
  - `309:f32`는 yaw처럼 보이는 상관성이 가장 강했다.
  - 그래도 reverse / teleport 시나리오까지 포함해 authoritative yaw라고 부를 만큼 증거가 충분하지 않았다.
  - `325:f32`는 steering-like 또는 turn-rate-like 필드일 가능성이 더 높아 보였다.
  - 결론: 이번 세션에서도 **둘 다 채택하지 않았다.**
- decoder가 이제 absolute-position discontinuity를 감지한다.
  - 기본 임계값: `absolute_discontinuity_distance_m = 25.0`
  - 큰 jump가 보이면 anchor / held heading / reference heading을 reset한다.
  - 그 프레임은 `anchored_local_pending_heading`으로 돌아가고 local pose를 원점부터 다시 잡는다.
- teleport/recover capture에서 실제 reset 이벤트를 확인했다.
  - `discontinuity_distance_m ~= 231.67`
  - `anchor_reset_reason = absolute_position_jump`
  - `anchor_reset_count = 1`
- `inspect_telemetry.py`와 recorder가 아래를 실제로 출력/저장한다.
  - `heading_source`
  - `anchor_locked`
  - `discontinuity_detected`
  - `discontinuity_distance_m`
  - `anchor_reset_count`
  - `anchor_reset_reason`

### 이 세션에서 그대로 다시 확인된 것
- replay shadow mode 동작
- `SCSTelemetrySharedv2_ats` live mapping decode 성공
- ATS-backed shadow loop 자체는 실제로 돈다
- 300-step bring-up 샘플은 여전히 안정적으로 재현 가능하다

## 구현돼 있고 실제로 돌아간 것

- replay telemetry source
- HTTP JSON telemetry source
- `shared_memory_v2` telemetry source
- shared-memory raw capture / candidate analysis tooling
- startup summary / startup validation
- replay recorder
- map matcher / preview path / speed planner / safety arbiter
- replay shadow mode
- ATS-backed shadow mode
- authoritative absolute pose -> anchored-local shadow path
- discontinuity detection + anchor reset path

## `shared_memory_v2` 현재 구현 상태

선택한 live path는 명확하다.

- plugin: `atssharedplugin64v2.dll`
- mapping: `SCSTelemetrySharedv2_ats`
- 자세한 계약 메모: `docs/SHARED_MEMORY_V2_DESIGN.md`

현재 reader가 decode하는 값:
- `speed_mps`
- `engine_rpm`
- `gear`
- `displayed_gear`
- `throttle`
- `speed_limit_kph` 후보
- `route_distance_km` 후보
- `route_time_min` 후보
- `world_x/world_y/world_z` absolute pose
- anchored-local pose
- absolute-position-derived heading
- discontinuity / anchor reset state

현재 reader가 아직 못 하는 것:
- authoritative paused/game-state field 확정
- authoritative game tick 복원
- authoritative yaw field 자체의 direct offset 확정

그래서 현재 `TelemetryFrame.game_tick`은 진짜 game tick이 아니라 **raw mapping crc32 기반 update token**이다.

## 솔직한 현재 상태

이 저장소는 이제 아래까지는 실제로 검증됐다.

- replay shadow mode
- live telemetry probe
- authoritative absolute position decode
- reverse / turn / teleport capture workflow
- discontinuity reset 이벤트 검출
- 300-step ATS-backed shadow run

하지만 아직 아래는 검증 주장 금지다.

- ATS 실제 월드 그래프와의 global map alignment
- HUD calibration 실사용
- control plugin write
- Active Mode
- turn-heavy longer live shadow reliability

## live shadow 현재 품질

좋아진 점:
- 초기 heading lock이 안정적이다.
- teleport/recover jump 뒤 stale anchor를 끌고 가지 않는다.
- straight / light-turn bring-up 구간에선 toy graph 기준 matching이 안정적이다.

아직 부족한 점:
- longer run이 driving pattern에 따라 아직 갈린다.
- turn-heavy 500-step run 요약:
  - `safety`: `NONE=266`, `MATCH_LOST=234`
  - 첫 `MATCH_LOST`: step `267`
  - `heading_source`: `absolute_position_delta=323`, `absolute_position_hold=174`, `velocity_direction=3`
  - `match_min ~= 0.891`
  - `cross_track_error_m max ~= 9.18`
  - `route_min ~= 0.579`
- straight/stop-heavy 500-step run 요약:
  - `safety`: `NONE=500`
  - `anchor_reset_events = 0`
  - `heading_source`: `absolute_position_delta=150`, `absolute_position_hold=347`, `velocity_direction=3`
  - `match_min = 1.00`
  - `cross_track_error_m max ~= 0.289`
  - `route_min ~= 0.699`

즉, 이번 세션의 성과는 telemetry semantics와 reset safety를 더 강하게 만든 거고, longer turn-heavy live matching 자체를 끝냈다는 뜻은 아니다.

## 중요한 caveat

- 현재 `data/maps/cache/default_graph.json`은 실제 ATS 월드 그래프가 아니라 작은 toy graph다.
- 그래서 `anchored_local`은 **ATS absolute world를 toy graph local frame에 맞추는 디버그/bring-up 프레임**이다.
- 이번 세션의 개선은 heading semantics와 discontinuity safety를 올린 것이지, 아직 “실제 ATS 도로 네트워크 전체를 따라간다”는 뜻은 아니다.

## 코드상 존재하지만 아직 실환경 미검증인 것

- `json_http` telemetry endpoint의 실제 ATS plugin 호환성
- `scscontroller` 기반 control sink
- DXcam 기반 HUD capture
- HUD preset 실제 캘리브레이션
- authoritative paused / world-state 필드
- authoritative direct yaw field

## 현재 가장 큰 기술 부채

- `309:f32`는 가장 유력한 yaw 후보지만 아직 계약으로 승격할 정도로 강한 증거가 없다.
- `325:f32`는 yaw보다 steering/turn-rate-like 필드일 가능성이 높다.
- 현재 heading은 direct yaw field가 아니라 `absolute_position_delta` + `absolute_position_hold` 전략이다.
- 실제 ATS map exporter가 없어서, 지금 matcher 개선은 toy graph 기준 bring-up 품질 확인에 머문다.
- control path는 telemetry semantics와 pose 품질이 더 solid해진 뒤 다음 단계로 가야 한다.
