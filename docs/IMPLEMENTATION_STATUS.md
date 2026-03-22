# Implementation Status

## 2026-03-22 실제 검증 스냅샷

### 이번 세션에서 로컬로 새로 확인된 것
- `SCSTelemetrySharedv2_ats` mapping이 ATS 실행 중 실제로 visible
- `atssharedplugin64v2.dll`가 ATS에서 실제로 load됨
- `shared_memory_v2` direct reader 구현 완료
- `scripts/inspect_telemetry.py --config configs/live_probe_moza_shared_memory.yaml --frames 5`에서 live decode 성공
- decode된 live 요약:
  - `game_tag='ats'`
  - `speed_mps`, `engine_rpm`, `gear`, `throttle`, `speed_limit_kph`, `route_distance_km`, `route_time_min` 읽힘
  - update token 변화 확인
- `ats-cinepilot run --config configs/live_probe_moza_shared_memory.yaml --mode shadow --steps 30` 성공
- 첫 **ATS-backed Shadow Mode** 실행 성공
- recorder 파일 생성 확인: `data/logs/live_probe_moza_shadow.jsonl`

### 이 세션에서 그대로 다시 확인된 것
- `scripts/setup_venv.ps1` 성공
- editable install 성공
- `pytest -q` 통과
- `ruff check .` 통과
- replay config validation 성공
- replay shadow smoke 성공

## 구현돼 있고 실제로 돌아간 것

- replay telemetry source
- HTTP JSON telemetry source
- `shared_memory_v2` telemetry source
- startup summary / startup validation
- replay recorder
- map matcher / preview path / speed planner / safety arbiter
- replay shadow mode
- ATS-backed shadow mode

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
- velocity 적분 기반 relative pose

현재 reader가 아직 못 하는 것:
- authoritative absolute world `x/z`
- authoritative paused/game-state field 확정
- authoritative game tick 복원

그래서 현재 `TelemetryFrame.game_tick`은 진짜 game tick이 아니라 **raw mapping crc32 기반 update token**이다.

## 솔직한 현재 상태

이 저장소는 이제 아래까지는 실제로 검증됐다.

- replay shadow mode
- live telemetry probe
- first ATS-backed shadow loop

하지만 아직 아래는 검증 주장 금지다.

- absolute pose 기반 정밀 map alignment
- HUD calibration 실사용
- control plugin write
- Active Mode

## 코드상 존재하지만 아직 실환경 미검증인 것

- `json_http` telemetry endpoint의 실제 ATS plugin 호환성
- `scscontroller` 기반 control sink
- DXcam 기반 HUD capture
- HUD preset 실제 캘리브레이션
- 실제 장시간 highway shadow stability

## 현재 가장 큰 기술 부채

- `shared_memory_v2`가 현재는 relative pose만 주기 때문에 map matching은 데모/bring-up 수준이다
- absolute world position 계약을 확정해야 진짜 route-following shadow 품질을 판단할 수 있다
- control path는 telemetry가 solid해진 뒤 다음 단계로 가야 한다
