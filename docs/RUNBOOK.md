# Runbook

## 반복 사이클

1. `.\scripts\setup_venv.ps1`
2. `ats-cinepilot check-config --config ...`
3. `python scripts\inspect_telemetry.py --config ...`
4. replay shadow smoke
5. real graph cache가 필요하면 export
6. 필요한 경우 controlled capture
7. capture -> replay 변환과 toy/real A/B
8. live shadow run
9. 로그 요약
10. HUD / controls / Active Mode는 그 다음

## 우선순위

### 1단계
- live telemetry stability
- absolute pose semantics 확인
- real graph alignment 확인
- matcher diagnostics 확인

### 2단계
- lane-accurate ATS graph 확보
- turn-heavy live shadow 재검증
- 필요할 때만 yaw field 재조사

### 3단계
- HUD route hint
- control plugin path
- Active Mode 전용 safety hardening

## 로컬 codex 작업 원칙

- 한 번에 한 층만 건드려
- 변경 후 바로 smoke test
- replay와 live를 둘 다 다시 확인해
- confidence가 낮으면 해제부터 강화해
- 딥러닝 모델은 나중

## PR Workflow

- 항상 `main`에서 `codex/` 브랜치를 새로 만들어
- 항상 PR을 열고 리뷰 가능한 diff 상태로 남겨
- 리뷰 없이 self-merge 하지 마
- PR 본문에는 정확한 명령어와 실제 결과를 그대로 적어

## 현재 선택된 real graph 경로

- source/toolchain: `truckermudgeon/maps` 공개 `usa-graph-demo.json`
- runtime config: `configs/live_probe_ats_real_graph.yaml`
- cache artifact: `data/maps/cache/ats_usa_region_real_graph_8km.json`
- alignment mode: `ats_absolute_identity`

중요:
- 이 graph는 public demo graph라서 coarse하다.
- ATS absolute pose와 같은 좌표계에는 올라오지만, lane/path 수준 route-following 품질을 보장하지 않는다.

## 실제 해석 규칙

### `inspect_telemetry.py`
- `telemetry status: telemetry ready`
  - mapping visible + decode 성공 + sampled frame update token 변화 확인
- `mapping visible but unsupported layout`
  - mapping은 열렸지만 이 reader가 아는 layout이 아님
- `mapping visible but stale/non-updating`
  - mapping은 열렸지만 sampled frame이 안 바뀜
- 기본 live config:
  - toy graph bring-up: `configs/live_probe_ats_toy_graph.yaml`
  - real graph validation: `configs/live_probe_ats_real_graph.yaml`
- 현재 기본 absolute pose 계약:
  - `285:f64` -> `world_x`
  - `293:f64` -> `world_y`
  - `301:f64` -> `world_z`

### real graph export

실주행 위치 근처 8km graph cache를 다시 만들 때:

```powershell
.\.venv\Scripts\python scripts\export_map.py --source trucksim-demo --input https://truckermudgeon.github.io/usa-graph-demo.json --output data\maps\cache\ats_usa_region_real_graph_8km.json --center-from-config configs\live_probe_moza_shared_memory.yaml --crop-radius-m 8000 --compact
```

확인 포인트:
- `graph_source = trucksim_demo_graph_region`
- `alignment_mode = ats_absolute_identity`
- `crop_center_x_m / crop_center_z_m`가 현재 ATS 위치 근처인지

### raw capture / replay A/B

capture:

```powershell
.\.venv\Scripts\python scripts\capture_shared_memory_v2.py --config configs\live_probe_moza_shared_memory.yaml --seconds 15 --hz 10 --delay 10 --label straight_light_turn_ab
.\.venv\Scripts\python scripts\capture_shared_memory_v2.py --config configs\live_probe_moza_shared_memory.yaml --seconds 20 --hz 10 --delay 10 --label turn_heavy_ab
```

같은 raw capture를 두 pose frame replay로 변환:

```powershell
.\.venv\Scripts\python scripts\convert_shared_memory_v2_capture_to_replay.py --input data\captures\shared_memory_v2\<capture>.jsonl --output data\replays\<name>_anchor.jsonl --config configs\live_probe_moza_shared_memory.yaml --pose-frame-mode anchored_local
.\.venv\Scripts\python scripts\convert_shared_memory_v2_capture_to_replay.py --input data\captures\shared_memory_v2\<capture>.jsonl --output data\replays\<name>_world.jsonl --config configs\live_probe_moza_shared_memory.yaml --pose-frame-mode world_absolute
```

replay recording이 필요할 때:

```powershell
.\.venv\Scripts\python scripts\record_telemetry_replay.py --config configs\live_probe_ats_real_graph.yaml --output data\replays\live_real_graph_check.jsonl --seconds 20 --hz 10
```

toy / real A/B run:

```powershell
.\.venv\Scripts\ats-cinepilot run --config configs\live_probe_ats_toy_graph.yaml --config data\debug\<toy_override>.yaml --mode shadow --steps 150
.\.venv\Scripts\ats-cinepilot run --config configs\live_probe_ats_real_graph.yaml --config data\debug\<real_override>.yaml --mode shadow --steps 150
```

요약:

```powershell
.\.venv\Scripts\python scripts\summarize_shadow_log.py --input data\logs\ab_straight_toy.jsonl --input data\logs\ab_straight_real.jsonl --input data\logs\ab_turn_toy.jsonl --input data\logs\ab_turn_real.jsonl --json data\debug\ab_summary.json
```

현재까지의 해석:
- toy graph는 local bring-up에는 유리하지만 실제 ATS global geometry를 대표하지 않는다.
- real graph는 continuous coverage를 보여주지만, public demo graph가 coarse해서 route confidence가 낮다.

### `ats-cinepilot run ... --mode shadow`

startup summary에서 최소 아래를 본다:
- `telemetry_source`
- `mapping`
- `control_sink`
- `route_provider`
- `hud_capture`
- `graph_source`
- `alignment_mode`

live shadow 성공 기준:
- 앱이 예외 없이 step loop를 돈다
- `fresh_ms`가 stale로 치솟지 않는다
- recorder가 생성된다
- real graph run이면 `pose=authoritative_absolute/world_absolute`
- `graph_failures=None`이 유지된다
- `nearest_edge_distance_m`가 합리적인 범위에 머문다

주의:
- real graph에서 `MATCH_LOST`가 나와도 바로 pose 계약이 틀렸다고 결론내리면 안 된다.
- 먼저 `graph_failures`, `nearest_edge_distance_m`, `candidate_count`, `route_confidence`를 같이 봐야 한다.

### 현재 확인된 실그래프 결과

live probe:

```powershell
.\.venv\Scripts\python scripts\inspect_telemetry.py --config configs\live_probe_ats_real_graph.yaml --frames 3
```

실제 결과:
- mapping visible
- decode 성공
- `pose_source=authoritative_absolute`
- `pose_frame=world_absolute`

ATS-backed real-graph shadow sample:
- `steps=200`
- `safety={MATCH_LOST: 95, ROUTE_CONFIDENCE_LOW: 105}`
- `match=[0.951, 1.000]`
- `route=[0.404, 0.500]`
- `cte_max=3.301`
- `near=[0.005, 3.301]`
- `cand=[8, 21]`
- `graph_failures={None: 200}`

해석:
- spatial coverage는 유지됐다.
- 현재 병목은 real graph geometry/route fidelity다.

### `inspect_controls.py`

- 아직 telemetry 다음 단계다
- `module import: FAILED`면 Python 쪽 `scscontroller.py`가 아직 없다
- dry-run은 안전하지만, 이것만으로 ATS가 실제로 명령을 수신한다고 증명되지는 않는다
