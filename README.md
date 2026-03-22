# ATS CinePilot

ATS에서 **안전하게 bring-up 가능한 cinematic shadow autopilot**을 만드는 프로젝트 스캐폴드야.

핵심 방향은 이거다.

- 순수 화면 AI보다 **텔레메트리 + 도로 그래프 + HUD 경로 힌트 + 규칙 기반 제어기** 구조를 우선한다.
- 첫 목표는 flashy한 Active Mode가 아니라 **실제 live telemetry ingest + 안정적인 Shadow Mode**다.
- MOZA R3는 v1에선 **수동 takeover 장치**로 취급한다.
- control path와 Active Mode는 telemetry semantics가 solid해진 뒤에만 건드린다.

## 지금 실제로 확인된 것

- replay shadow mode 동작
- editable install / pytest / ruff 통과
- `SCSTelemetrySharedv2_ats` live mapping decode 성공
- authoritative absolute pose 계약 일부 확인
  - `285:f64` -> `world_x`
  - `293:f64` -> `world_y`
  - `301:f64` -> `world_z`
- ATS-backed Shadow Mode bring-up 성공
  - `ats-cinepilot run --config configs/live_probe_moza_shared_memory.yaml --mode shadow --steps 300`
  - `safety=NONE` 300/300
  - `match_confidence` 최소값 `1.00`
  - `cross_track_error_m` 최대값 `0.046`
- reverse / turn / teleport capture workflow 실제 검증
- teleport/recover jump 시 anchor reset 실제 검증

## 아직 확인 안 된 것

- authoritative direct yaw field offset
- 실제 ATS global road graph alignment
- longer turn-heavy shadow reliability
- HUD calibration 실사용
- `scs-sdk-controller` 기반 control write
- Active Mode

## 중요한 현실 체크

현재 기본 map cache `data/maps/cache/default_graph.json`은 실제 ATS 월드 그래프가 아니라 toy graph다.

그래서 지금 성공한 live shadow 품질은:
- telemetry가 실제로 들어온다
- absolute pose semantics가 훨씬 명확해졌다
- toy graph 기준 anchored-local matching이 안정적이다

라는 뜻이지, 아직 “실제 ATS 도로 네트워크 전체를 따라간다”는 뜻은 아니다.

## 폴더 구조

```text
ats_cinepilot_handoff/
├─ configs/
├─ data/
├─ docs/
├─ scripts/
├─ src/ats_cinepilot/
└─ tests/
```

## 추천 작업 순서

1. `docs/CODEX_HANDOFF.md` 먼저 읽기
2. `.\scripts\setup_venv.ps1`
3. `ats-cinepilot check-config --config configs/profiles/replay_demo.yaml`
4. `ats-cinepilot run --config configs/profiles/replay_demo.yaml --mode shadow --steps 300`
5. `ats-cinepilot check-config --config configs/live_probe_moza_shared_memory.yaml`
6. `python scripts/inspect_telemetry.py --config configs/live_probe_moza_shared_memory.yaml --frames 8`
7. 필요하면 `python scripts/capture_shared_memory_v2.py ...`
8. `ats-cinepilot run --config configs/live_probe_moza_shared_memory.yaml --mode shadow --steps 300`
9. 그다음에만 HUD / controls / Active Mode 범위로 이동

## 빠른 시작 예시

```powershell
.\scripts\setup_venv.ps1
.\.venv\Scripts\ats-cinepilot check-config --config configs\profiles\replay_demo.yaml
.\.venv\Scripts\ats-cinepilot run --config configs\profiles\replay_demo.yaml --mode shadow --steps 300
.\.venv\Scripts\ats-cinepilot check-config --config configs\live_probe_moza_shared_memory.yaml
.\.venv\Scripts\python scripts\inspect_telemetry.py --config configs\live_probe_moza_shared_memory.yaml --frames 8
.\.venv\Scripts\ats-cinepilot run --config configs\live_probe_moza_shared_memory.yaml --mode shadow --steps 300
```

## 현재 선택된 live telemetry 경로

- plugin DLL: `atssharedplugin64v2.dll`
- mapping name: `SCSTelemetrySharedv2_ats`
- config: `configs/live_probe_moza_shared_memory.yaml`
- design note: `docs/SHARED_MEMORY_V2_DESIGN.md`

reader는 현재 아래를 사용한다.

- absolute position: `285/293/301`
- heading: `absolute_position_delta` + `absolute_position_hold`
- pose frame: 기본 `anchored_local`
- discontinuity reset: `absolute_discontinuity_distance_m = 25.0`

`309:f32`, `325:f32`는 direct yaw 후보로 조사했지만 아직 채택하지 않았다.

## 도구

live probe:

```powershell
.\.venv\Scripts\python scripts\inspect_telemetry.py --config configs\live_probe_moza_shared_memory.yaml --frames 8 --save-json data\debug\shared_memory_v2_probe.json
```

raw capture:

```powershell
.\.venv\Scripts\python scripts\capture_shared_memory_v2.py --config configs\live_probe_moza_shared_memory.yaml --seconds 6 --hz 10 --delay 3 --label straight_absolute_anchor
```

offset analysis:

```powershell
.\.venv\Scripts\python scripts\analyze_shared_memory_v2_capture.py --input data\captures\shared_memory_v2 --inspect 285:f64 --inspect 293:f64 --inspect 301:f64 --inspect 309:f32 --inspect 325:f32 --summary-json data\debug\shared_memory_v2_capture_summary.json --scenario-summary-csv data\debug\shared_memory_v2_scenarios.csv --candidate-summary-csv data\debug\shared_memory_v2_candidates.csv --heading-summary-csv data\debug\shared_memory_v2_heading_candidates.csv
```

권장 capture suite:

```powershell
.\.venv\Scripts\python scripts\capture_shared_memory_v2.py --config configs\live_probe_moza_shared_memory.yaml --seconds 8 --hz 10 --label full_stop
.\.venv\Scripts\python scripts\capture_shared_memory_v2.py --config configs\live_probe_moza_shared_memory.yaml --seconds 8 --hz 10 --delay 3 --label slow_left_turn
.\.venv\Scripts\python scripts\capture_shared_memory_v2.py --config configs\live_probe_moza_shared_memory.yaml --seconds 8 --hz 10 --delay 3 --label slow_right_turn
.\.venv\Scripts\python scripts\capture_shared_memory_v2.py --config configs\live_probe_moza_shared_memory.yaml --seconds 8 --hz 10 --delay 3 --label reverse
.\.venv\Scripts\python scripts\capture_shared_memory_v2.py --config configs\live_probe_moza_shared_memory.yaml --seconds 15 --hz 10 --delay 3 --label teleport_recover
```

## 외부 의존성

이 저장소 안에는 외부 프로젝트의 바이너리나 코드를 번들하지 않았다.

필요할 가능성이 높은 외부 요소는 문서에 정리해뒀다.

- SCS Telemetry SDK / 텔레메트리 플러그인
- `scs-sdk-controller`
- `truckermudgeon/maps` 또는 `ts-map`
- DXcam

## 문서 맵

- `docs/CODEX_HANDOFF.md`
- `docs/ARCHITECTURE.md`
- `docs/IMPLEMENTATION_STATUS.md`
- `docs/LOCAL_SETUP.md`
- `docs/PLUGIN_OPTIONS.md`
- `docs/RESEARCH_NOTES.md`
- `docs/SHARED_MEMORY_V2_DESIGN.md`
- `docs/RUNBOOK.md`
- `docs/SAFETY.md`
