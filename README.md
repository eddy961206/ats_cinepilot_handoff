# ATS CinePilot

ATS에서 **안전하게 bring-up 가능한 cinematic shadow autopilot**을 만드는 프로젝트 스캐폴드야.

핵심 방향은 이거다.

- 순수 화면 AI보다 **텔레메트리 + 도로 그래프 + HUD 경로 힌트 + 규칙 기반 제어기** 구조를 우선한다.
- 첫 목표는 flashy한 Active Mode가 아니라 **실제 live telemetry ingest + 안정적인 Shadow Mode**다.
- MOZA R3는 v1에선 **수동 takeover 장치**로 취급한다.
- control path와 Active Mode는 telemetry semantics와 graph alignment가 solid해진 뒤에만 건드린다.

## 지금 실제로 확인된 것

- replay shadow mode 동작
- editable install / pytest / ruff 통과
- `SCSTelemetrySharedv2_ats` live mapping decode 성공
- authoritative absolute pose 계약 일부 확인
  - `285:f64` -> `world_x`
  - `293:f64` -> `world_y`
  - `301:f64` -> `world_z`
- ATS-backed Shadow Mode bring-up 성공
- ATS absolute pose를 실그래프 후보와 붙이는 real graph path 연결
  - source/toolchain: `truckermudgeon/maps` 공개 `usa-graph-demo.json`
  - alignment: `ats_absolute_identity`
- toy graph vs real graph A/B 비교 가능
- ATS-backed real-graph shadow sample 실제 검증
  - `steps=200`
  - `match=[0.951, 1.000]`
  - `cte_max=3.301`
  - `graph_failures={None: 200}`

## 아직 확인 안 된 것

- authoritative direct yaw field offset
- lane-accurate real ATS world graph
- real graph 기준 route confidence가 충분한 shadow reliability
- HUD calibration 실사용
- `scs-sdk-controller` 기반 control write
- Active Mode

## 중요한 현실 체크

현재 실그래프 경로는 연결됐지만, 선택한 공개 graph artifact는 **coarse demo graph**다.

그래서 지금 성공한 실그래프 검증은:
- telemetry가 실제로 들어온다
- absolute pose가 공개 ATS graph와 같은 좌표계에 올라온다
- turn-heavy에서도 graph coverage가 유지된다

라는 뜻이지, 아직 “실제 ATS 도로 네트워크 전체를 lane/path 수준으로 따라간다”는 뜻은 아니다.

현재 dominant bottleneck은 yaw보다 **graph fidelity**다.

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
5. `ats-cinepilot check-config --config configs/live_probe_ats_real_graph.yaml`
6. `python scripts/inspect_telemetry.py --config configs/live_probe_ats_real_graph.yaml --frames 3`
7. 필요하면 `python scripts/export_map.py ...`
8. `ats-cinepilot run --config configs/live_probe_ats_real_graph.yaml --mode shadow --steps 300`
9. 그다음에만 HUD / controls / Active Mode 범위로 이동

## 빠른 시작 예시

```powershell
.\scripts\setup_venv.ps1
.\.venv\Scripts\ats-cinepilot check-config --config configs\profiles\replay_demo.yaml
.\.venv\Scripts\ats-cinepilot run --config configs\profiles\replay_demo.yaml --mode shadow --steps 300
.\.venv\Scripts\ats-cinepilot check-config --config configs\live_probe_ats_real_graph.yaml
.\.venv\Scripts\python scripts\inspect_telemetry.py --config configs\live_probe_ats_real_graph.yaml --frames 3
.\.venv\Scripts\python scripts\export_map.py --source trucksim-demo --input https://truckermudgeon.github.io/usa-graph-demo.json --output data\maps\cache\ats_usa_region_real_graph_8km.json --center-from-config configs\live_probe_moza_shared_memory.yaml --crop-radius-m 8000 --compact
.\.venv\Scripts\ats-cinepilot run --config configs\live_probe_ats_real_graph.yaml --mode shadow --steps 300
```

## 현재 선택된 live telemetry 경로

- plugin DLL: `atssharedplugin64v2.dll`
- mapping name: `SCSTelemetrySharedv2_ats`
- config: `configs/live_probe_moza_shared_memory.yaml`
- design note: `docs/SHARED_MEMORY_V2_DESIGN.md`

reader는 현재 아래를 사용한다.

- absolute position: `285/293/301`
- heading: `absolute_position_delta` + `absolute_position_hold`
- discontinuity reset: `absolute_discontinuity_distance_m = 25.0`

`309:f32`, `325:f32`는 direct yaw 후보로 조사했지만 아직 채택하지 않았다.

## 현재 선택된 real graph 경로

- config: `configs/live_probe_ats_real_graph.yaml`
- cache: `data/maps/cache/ats_usa_region_real_graph_8km.json`
- source/toolchain: `truckermudgeon/maps` 공개 `usa-graph-demo.json`
- alignment mode: `ats_absolute_identity`

이 경로는 toy graph 대신 ATS absolute pose를 실그래프 후보와 비교할 때 쓴다.

## A/B 비교 도구

같은 raw shared-memory capture로 toy graph와 real graph를 비교하는 흐름을 추가해뒀다.

raw capture:

```powershell
.\.venv\Scripts\python scripts\capture_shared_memory_v2.py --config configs\live_probe_moza_shared_memory.yaml --seconds 15 --hz 10 --delay 10 --label straight_light_turn_ab
```

replay 변환:

```powershell
.\.venv\Scripts\python scripts\convert_shared_memory_v2_capture_to_replay.py --input data\captures\shared_memory_v2\<capture>.jsonl --output data\replays\<name>_anchor.jsonl --config configs\live_probe_moza_shared_memory.yaml --pose-frame-mode anchored_local
.\.venv\Scripts\python scripts\convert_shared_memory_v2_capture_to_replay.py --input data\captures\shared_memory_v2\<capture>.jsonl --output data\replays\<name>_world.jsonl --config configs\live_probe_moza_shared_memory.yaml --pose-frame-mode world_absolute
```

요약:

```powershell
.\.venv\Scripts\python scripts\summarize_shadow_log.py --input data\logs\ab_straight_toy.jsonl --input data\logs\ab_straight_real.jsonl --input data\logs\ab_turn_toy.jsonl --input data\logs\ab_turn_real.jsonl --json data\debug\ab_summary.json
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
