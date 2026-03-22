# Implementation Status

## 2026-03-22 실제 검증 스냅샷

### 이번 세션에서 로컬로 확인된 것
- `scripts/setup_venv.ps1` 실행 성공
- editable install 성공: `pip install -e ".[dev,windows]"`
- 전체 테스트 통과: `pytest -q` -> `11 passed`
- `ats-cinepilot check-config --config configs/profiles/replay_demo.yaml` 성공
- `scripts/replay_session.py --config configs/profiles/replay_demo.yaml --steps 5` 성공
- `ats-cinepilot run --config configs/profiles/replay_demo.yaml --mode shadow --steps 5` 성공
- replay shadow 실행 시 step별 상태 로그 출력 확인
- replay recorder에 `effective_hint`, `telemetry_freshness_ms`, `selected_branch`, `speed_target_mps` 기록 확인
- `inspect_telemetry.py`가 HTTP probe 실패와 `Local\SCSTelemetry` 가시성 부재를 명시적으로 출력함
- `inspect_controls.py`가 `scscontroller` import 실패를 명시적으로 출력함
- ATS 설치 경로 확인: `D:\Steam\steamapps\common\American Truck Simulator`
- ATS plugin 확인: `atssharedplugin64v2.dll` 존재
- ATS 실행 중 `game.log.txt`에서 `atssharedplugin64v2.dll` load 확인
- 선택한 live telemetry 경로 확인: `SCSTelemetrySharedv2`
- 실제 live probe 결과:
  - ATS는 실행 중이었음
  - plugin DLL은 존재했음
  - `SCSTelemetrySharedv2`는 열리지 않았음
  - 현재 상태는 "plugin loaded, shared memory not initialized yet"
- 실제 control probe 결과:
  - `scscontroller` Python module 없음
  - `scs_sdk_controller.dll` 없음
  - CMake / MSVC `cl` 없음

## 구현돼 있고 이번 세션에 다시 확인한 것
- config merge 로더
- replay telemetry source
- generic HTTP JSON telemetry source
- dynamic-module control sink
- DXcam / MSS capture wrapper
- HUD preset loader
- route mask / turn bias 추출 초안
- graph cache / spatial index / matcher
- branch selector / preview path / speed planner
- pure pursuit / PID speed controller
- safety arbiter
- replay recorder / overlay

## 이번 세션에 실질적으로 개선된 것
- `configs/profiles/replay_demo.yaml`가 이제 단독 실행 가능
- config 파일에 `extends` 지원 추가
- `check-config`가 파일 존재/필수 필드 기준으로 검증하도록 강화
- startup summary 추가
- replay shadow mode에 step 상태 로그 추가
- route confidence fallback 추가
  - HUD가 없어도 비분기 구간에서는 map continuity 기반으로 shadow 평가 가능
  - 분기 ambiguity에서는 confidence를 낮게 유지
- telemetry freshness 추적 추가
- control mapping 기본값 수정
  - `throttle -> aforward`
  - `brake -> abackward`
  - `left_blinker -> lblinker`
  - `right_blinker -> rblinker`
- inspect 스크립트가 Windows named shared memory probe를 지원
- live diagnostics 분류 추가
  - ATS not running
  - plugin missing
  - named shared memory missing
  - Python control module missing
  - field mapping mismatch
  - probable permission/environment issue
- live probe 전용 config 추가: `configs/live_probe_moza_shared_memory.yaml`
- `telemetry.source=shared_memory_v2`를 `run`에 넣으면 지금은 early-fail 하도록 명시
  - direct reader가 아직 없다는 사실을 숨기지 않도록 함

## 코드상 존재하지만 아직 실환경 미검증인 것
- `json_http` telemetry endpoint의 실제 ATS 플러그인 스키마 적합성
- `scscontroller` 기반 control write가 ATS 1.58에서 실제로 반영되는지
- DXcam 캡처가 ATS 창에서 안정적으로 동작하는지
- HUD preset 2종의 실제 Route Advisor 위치 적합성
- speed / steering gain 실차(게임) 튜닝
- map adapter가 실제 exporter JSON과 맞는지

## 아직 없는 것 또는 솔직히 스텁인 것
- `Local\SCSTelemetry` 바이너리 구조를 직접 읽는 shared-memory telemetry reader
- real wheel/hotkey manual override
- direct route provider
- lead vehicle / ACC
- 교차로 복잡 분기 처리 고도화
- map mod별 adapter 정교화

## 현재 실제 상태 평가

이 저장소는 이제 **로컬 replay shadow mode를 바로 돌리고 관찰할 수 있는 상태**까지는 올라왔다.

하지만 ATS 실환경 기준으로는 아직 아래가 남아 있다.
- `SCSTelemetrySharedv2` direct reader를 구현하거나, 현재 shared-memory path와 동등한 live reader를 확정해야 함
- `scs-sdk-controller` plugin + `scscontroller.py`를 실제로 설치해야 함
- HUD calibration은 실제 스크린샷으로 다시 맞춰야 함
- active mode는 아직 검증 주장 금지

### 현재 가장 정확한 live blocker
- ATS 메인 메뉴에서 확장 SDK 기능 확인 팝업이 떠 있는 상태였고, 그 상태에선 `SCSTelemetrySharedv2`가 열리지 않았다.
- 따라서 이번 세션의 실제 결론은:
  - live telemetry **경로 선택은 완료**
  - ATS-backed **실 probe는 성공**
  - 첫 live shadow run은 **shared memory 미초기화 + direct reader 부재**로 차단
