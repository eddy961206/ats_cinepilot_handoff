# Runbook

## 반복 사이클

1. `.\scripts\setup_venv.ps1`
2. `ats-cinepilot check-config --config ...`
3. `python scripts\inspect_telemetry.py --config ...`
4. replay shadow smoke
5. dense/coarse graph cache 준비
6. replay A/B
7. live shadow run
8. 로그 요약
9. graph fidelity가 충분해질 때까지 route source로 넘어가지 않기

## 현재 우선순위

### 1단계
- live telemetry stability
- absolute pose semantics 확인
- dense/coarse ATS graph alignment 확인
- matcher diagnostics 확인

### 2단계
- graph fidelity 개선
- turn-heavy 재검증
- 그래도 bottleneck이 남을 때만 route source

### 3단계
- HUD route hint
- control plugin path
- Active Mode

## PR Workflow

- 항상 `main` 기준 최신 상태를 확인해
- 이전 PR이 아직 merge 안 됐으면 stale `main`에서 새 기능 시작하지 마
- 항상 `codex/` 브랜치를 새로 만들어
- 항상 PR을 열고 리뷰 가능한 diff 상태로 남겨
- self-merge 하지 마
- PR 본문에는 정확한 명령어와 실제 결과를 그대로 적어

## dense local graph 준비

전제:
- ATS install: `D:\Steam\steamapps\common\American Truck Simulator`
- toolchain repo: `C:\workspaces\python_workspace\_ext\trucksim_maps_repo`

Build Tools:

```powershell
winget install --id Microsoft.VisualStudio.2022.BuildTools --exact --accept-package-agreements --accept-source-agreements --override "--wait --quiet --norestart --nocache --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended"
```

toolchain deps:

```powershell
cd C:\workspaces\python_workspace\_ext\trucksim_maps_repo
npm install
```

주의:
- Windows에선 `npm install` 마지막 `parser` symlink postinstall이 `EPERM`으로 죽을 수 있다.
- `cityhash.node`, `gdeflate.node`, `tsx`가 이미 생겼으면 dense export는 가능하다.
- runtime export는 `scripts/export_local_dense_graph.py`가 parser output을 재사용해서 focused ATS road GeoJSON과 runtime cache를 만든다.

## live telemetry probe

```powershell
.\.venv\Scripts\python scripts\inspect_telemetry.py --config configs\live_probe_ats_dense_local_graph.yaml --frames 3
```

상태 해석:
- `telemetry ready`
  - mapping visible + decode 성공
- `ATS not running`
  - ATS process가 꺼져 있음
- `plugin missing`
  - DLL이 plugin dir에 없음
- `mapping missing`
  - DLL은 있지만 shared memory가 안 열림

## dense local graph export

```powershell
.\.venv\Scripts\python scripts\export_local_dense_graph.py --config configs\live_probe_ats_real_graph.yaml --config configs\profiles\replay_ab_straight_light_turn.yaml --parser-output-dir "data\maps\trucksim_parser\ats_local" --geojson-output-dir "data\maps\trucksim_geojson\ats_local_region" --output-cache "data\maps\cache\ats_usa_region_dense_local_geojson_8km.json" --radius-m 8000
```

확인 포인트:
- `graph_source = trucksim_local_geojson_region`
- `alignment_mode = ats_absolute_identity`
- `node_count`, `edge_count`

## replay A/B

샘플 override:
- `configs/profiles/replay_ab_straight_light_turn.yaml`
- `configs/profiles/replay_ab_turn_heavy.yaml`
- `configs/profiles/replay_ab_quiet.yaml`

coarse vs dense replay:

```powershell
.\.venv\Scripts\ats-cinepilot run --config configs\live_probe_ats_real_graph.yaml --config configs\profiles\replay_ab_straight_light_turn.yaml --config configs\profiles\replay_ab_quiet.yaml --mode shadow
.\.venv\Scripts\ats-cinepilot run --config configs\live_probe_ats_dense_local_graph.yaml --config configs\profiles\replay_ab_straight_light_turn.yaml --config configs\profiles\replay_ab_quiet.yaml --mode shadow
.\.venv\Scripts\ats-cinepilot run --config configs\live_probe_ats_real_graph.yaml --config configs\profiles\replay_ab_turn_heavy.yaml --config configs\profiles\replay_ab_quiet.yaml --mode shadow
.\.venv\Scripts\ats-cinepilot run --config configs\live_probe_ats_dense_local_graph.yaml --config configs\profiles\replay_ab_turn_heavy.yaml --config configs\profiles\replay_ab_quiet.yaml --mode shadow
```

요약:

```powershell
.\.venv\Scripts\python scripts\summarize_shadow_log.py --input data\logs\ab_straight_toy.jsonl --input data\logs\replay_ab_straight_real_graph.jsonl --input data\logs\replay_ab_straight_dense_local_geojson_graph.jsonl --input data\logs\ab_turn_toy.jsonl --input data\logs\replay_ab_turn_real_graph.jsonl --input data\logs\replay_ab_turn_dense_local_geojson_graph.jsonl --json data\debug\dense_local_geojson_ab_summary.json
```

주의:
- toy graph는 `anchored_local`
- coarse/dense real graph는 `world_absolute`
- 그래서 toy를 coarse/dense와 **같은 replay 입력**으로 완전히 공정 비교할 수는 없다
- toy는 ATS-backed baseline, coarse/dense는 same-input replay로 비교한다

## 현재 해석

- toy graph 대비 real-graph family는 coverage가 훨씬 낫다
- dense local graph는 straight/light-turn에서는 coarse public graph보다 좋아졌지만, turn-heavy는 아직 불안정하다
- 그래서 다음 세션은 route source보다 graph fidelity가 우선이다

## live shadow run

```powershell
.\.venv\Scripts\ats-cinepilot run --config configs\live_probe_ats_dense_local_graph.yaml --mode shadow --steps 300
```

성공 기준:
- step loop가 예외 없이 돈다
- `fresh_ms`가 stale로 치솟지 않는다
- `graph_failures=None` 유지
- `nearest_edge_distance_m`가 합리적인 범위에 머문다

## 다음 액션 판단

- dense local graph가 coarse보다 확실히 좋아지면:
  - 그때 route source를 검토
- dense local graph가 coarse보다 여전히 비슷하거나 나쁘면:
  - route source로 가지 말고 graph geometry/toolchain을 다시 파기
