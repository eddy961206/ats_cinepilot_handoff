# Implementation Status

## 2026-03-22 실제 검증 스냅샷

### 이번 세션에서 로컬로 새로 확인된 것
- `SCSTelemetrySharedv2_ats`에서 authoritative absolute pose 후보를 실제로 다시 확인했다.
- 현재 선택된 absolute pose 계약:
  - `285:f64` -> `world_x`
  - `293:f64` -> `world_y`
  - `301:f64` -> `world_z`
- `scripts/capture_shared_memory_v2.py`로 raw mapping snapshot + decoded state를 실제로 수집했다.
- `scripts/analyze_shared_memory_v2_capture.py`로 offset 후보를 다시 비교했다.
- `shared_memory_v2` decoder가 이제:
  - authoritative absolute position을 읽고
  - `absolute_position_delta` 기반 heading을 만들고
  - 그 사이 프레임은 `absolute_position_hold`로 유지하고
  - 첫 valid absolute heading 이후에만 anchored-local heading을 lock한다.
- `scripts/inspect_telemetry.py --config configs/live_probe_moza_shared_memory.yaml --frames 8`에서 아래를 실제로 확인했다.
  - `pose_source=authoritative_absolute`
  - `pose_frame=anchored_local` 또는 초기 몇 프레임의 `anchored_local_pending_heading`
  - `heading_source=absolute_position_delta` / `absolute_position_hold`
  - `anchor_locked=yes`
- `ats-cinepilot run --config configs/live_probe_moza_shared_memory.yaml --mode shadow --steps 300`에서 실제 ATS-backed Shadow Mode 장시간 샘플을 다시 돌렸다.
  - `safety=NONE` 300/300
  - `match_confidence` 최소값 `1.00`
  - `cross_track_error_m` 최대값 `0.046`
  - `route_confidence` 최소값 `0.700`

### 이 세션에서 그대로 다시 확인된 것
- `scripts/setup_venv.ps1` 성공
- editable install 성공
- `pytest -q` 통과
- `ruff check .` 통과
- replay config validation 성공
- replay shadow smoke 성공
- `SCSTelemetrySharedv2_ats` mapping visible + decode 성공
- 첫 ATS-backed Shadow Mode bring-up이 이미 성공했음을 재확인

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

## `shared_memory_v2` 현재 구현 상태

선택한 live path는 이제 명확하다.

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
- 300-step ATS-backed shadow run

하지만 아직 아래는 검증 주장 금지다.

- ATS 실제 월드 그래프와의 global map alignment
- HUD calibration 실사용
- control plugin write
- Active Mode

## 중요한 caveat

- 현재 `data/maps/cache/default_graph.json`은 실제 ATS 월드 그래프가 아니라 작은 toy graph다.
- 그래서 `anchored_local`은 **ATS absolute world를 toy graph local frame에 맞추는 디버그/bring-up 프레임**이다.
- 이번 세션의 개선은 telemetry semantics와 pose 안정성은 크게 올렸지만, 아직 “실제 ATS 도로 네트워크 전체를 따라간다”는 뜻은 아니다.

## 코드상 존재하지만 아직 실환경 미검증인 것

- `json_http` telemetry endpoint의 실제 ATS plugin 호환성
- `scscontroller` 기반 control sink
- DXcam 기반 HUD capture
- HUD preset 실제 캘리브레이션
- 교차로/곡선/재배치 상황의 long-run absolute heading behavior

## 현재 가장 큰 기술 부채

- `309:f32`, `325:f32`는 heading/turn 관련 후보로 보이지만 아직 계약으로 채택하지 않았다.
- 현재 heading은 direct yaw field가 아니라 `absolute_position_delta` + `absolute_position_hold` 전략이다.
- 실제 ATS map exporter가 없어서, 지금 matcher 개선은 toy graph 기준 bring-up 품질 확인에 머문다.
- control path는 telemetry semantics가 충분히 solid해진 뒤 다음 단계로 가야 한다.
