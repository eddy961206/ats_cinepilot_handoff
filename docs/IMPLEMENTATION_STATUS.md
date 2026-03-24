# Implementation Status

## 2026-03-24 실제 검증 스냅샷

### 이번 세션 base 상태

- PR #5는 `main`에 merge돼 있었다.
- PR #6는 `codex/real-ats-world-graph-alignment`에만 merge돼 있었고 `main`에는 아직 없었다.
- 그래서 이번 작업 베이스는 `main`이 아니라 `origin/codex/real-ats-world-graph-alignment@04bf533`였다.
- 이번 브랜치는 그 위에 stacked로 올라간다.

### 이번 세션에서 새로 확인된 것

- baseline을 replay로 다시 재현했다.
  - straight/light-turn dense forward-only는 여전히 `heading≈π` 패턴
  - turn-heavy dense forward-only는 route confidence가 높아도 `MATCH_LOST`
- matcher direction diagnostics를 recorder와 summary까지 연결했다.
  - `selected_reason`
  - `direction_confidence_state`
  - top candidate snapshot
- matcher에 scoped reverse-heading rescue를 추가했다.
  - trigger:
    - opposed candidate인데 reverse heading으로는 opposed가 아닐 것
    - non-opposed 후보가 없거나, 그 후보보다 `map.reverse_heading_min_advantage_m` 만큼 더 가까울 것
  - current default:
    - `map.reverse_heading_min_advantage_m = 1.0`
    - `map.reverse_heading_penalty = 0.5`
- continuity bonus를 nearest candidate와의 거리 차로 gating했다.
  - current default:
    - `map.continuity_distance_slack_m = 1.0`
- matcher tuning 값을 config로 노출했다.
  - `map.heading_weight`
  - `map.distance_weight`
  - `map.hysteresis_weight`
  - `map.continuity_distance_slack_m`
  - `map.reverse_heading_min_advantage_m`
  - `map.reverse_heading_penalty`
- 2026-03-24 기준 live probe는 다시 돌렸지만 ATS가 꺼져 있었다.
  - result: `ATS not running`
- review에서 지적된 reverse-rescue semantics bug도 막았다.
  - `MatchedEdge`에 `travel_direction`을 추가
  - preview planner / branch selector / branch candidate count가 이 방향을 따라가도록 수정
  - 통합 테스트 `tests/test_preview_planner.py` 추가

## 현재 텔레메트리 계약

- mapping name: `SCSTelemetrySharedv2_ats`
- absolute pose:
  - `285:f64` -> `world_x`
  - `293:f64` -> `world_y`
  - `301:f64` -> `world_z`
- heading:
  - `absolute_position_delta`
  - `absolute_position_hold`
  - fallback `velocity_direction`
- discontinuity reset:
  - `absolute_discontinuity_distance_m = 25.0`

이 계약은 이번 세션에서도 유지했다. dense graph work 중 새로운 증거로 뒤집히지 않았다.

## 현재 선택된 그래프 경로

### toy baseline
- config: `configs/live_probe_ats_toy_graph.yaml`
- alignment: `anchored_local_toy_graph`

### coarse public real graph
- config: `configs/live_probe_ats_real_graph.yaml`
- cache: `data/maps/cache/ats_usa_region_real_graph_8km.json`
- source/toolchain: `truckermudgeon/maps` 공개 `usa-graph-demo.json`
- alignment: `ats_absolute_identity`

### dense local selected path
- config: `configs/live_probe_ats_dense_local_graph.yaml`
- cache: `data/maps/cache/ats_usa_region_dense_local_geojson_8km.json`
- source/toolchain: 로컬 ATS install + `_ext/trucksim_maps_repo`
- export mode: focused ATS road GeoJSON
- alignment: `ats_absolute_identity`

## dense local export 결과

command:

```powershell
.\.venv\Scripts\python scripts\export_local_dense_graph.py --config configs\live_probe_ats_real_graph.yaml --config configs\profiles\replay_ab_straight_light_turn.yaml --parser-output-dir "data\maps\trucksim_parser\ats_local" --geojson-output-dir "data\maps\trucksim_geojson\ats_local_region" --output-cache "data\maps\cache\ats_usa_region_dense_local_geojson_8km.json" --radius-m 8000
```

result metadata:
- `node_count = 2143`
- `edge_count = 2156`
- `graph_source = trucksim_local_geojson_region`
- `alignment_mode = ats_absolute_identity`
- `synthetic_reverse_edges = false`

현실 체크:
- local parser / geojson intermediate는 reproducible local artifact라 `.gitignore`로 제외했다.
- PR에는 runtime cache만 포함한다.

## baseline 재현

### straight/light-turn

- coarse public replay
  - input: ATS-backed `data/logs/ab_straight_real.jsonl`
  - `steps=150`
  - `safety={MATCH_LOST: 150}`
  - `first_MATCH_LOST=1`
  - `route=[0.419, 0.480]`
  - `cte_max=13.910`
- dense local geojson replay
  - same ATS-backed input
  - `steps=150`
  - `safety={MATCH_LOST: 150}`
  - `first_MATCH_LOST=1`
  - `route=[0.447, 0.622]`
  - `cte_max=8.651`
  - `match=[0.617, 0.901]`
  - `direction_confidence={confident: 1, opposed_best_available: 149}`

### turn-heavy

- coarse public replay
  - input: ATS-backed `data/logs/ab_turn_real.jsonl`
  - `steps=200`
  - `safety={MATCH_LOST: 165, ROUTE_CONFIDENCE_LOW: 35}`
  - `first_ROUTE_CONFIDENCE_LOW=80`
  - `route=[0.329, 0.499]`
  - `cte_max=9.680`
- dense local geojson replay
  - same ATS-backed input
  - `steps=200`
  - `safety={MATCH_LOST: 181, NONE: 19}`
  - `route=[0.482, 0.689]`
  - `cte_max=17.318`
  - `match=[0.706, 0.996]`
  - delayed continuity gap(`winner_distance - min_candidate_distance > 1m`) = `28`

## post-change A/B

### straight/light-turn

- coarse public replay
  - unchanged
  - `safety={MATCH_LOST: 150}`
  - `route=[0.419, 0.480]`
  - `cte_max=13.910`
- dense local geojson replay
  - `safety={MATCH_LOST: 135, NONE: 15}`
  - `first_MATCH_LOST=1`
  - `route=[0.622, 0.698]`
  - `match=[0.872, 0.995]`
  - `cte_max=8.651`
  - `direction_confidence={confident: 1, reverse_heading_rescued: 149}`

### turn-heavy

- coarse public replay
  - unchanged
  - `safety={MATCH_LOST: 165, ROUTE_CONFIDENCE_LOW: 35}`
  - `first_ROUTE_CONFIDENCE_LOW=80`
  - `route=[0.329, 0.499]`
  - `cte_max=9.680`
- dense local geojson replay
  - `safety={MATCH_LOST: 181, NONE: 19}`
  - `route=[0.482, 0.689]`
  - `match=[0.706, 0.996]`
  - `cte_max=17.318`
  - `direction_confidence={ambiguous: 10, confident: 156, reverse_heading_rescued: 34}`
  - delayed continuity gap(`winner_distance - min_candidate_distance > 1m`) = `6`

### 해석

- dense straight/light-turn은 pure heading mismatch가 아니라 cte 중심 문제로 이동했다.
- dense turn-heavy는 headline safety 분포가 그대로라서 아직 “문제가 풀렸다”고 말할 수 없다.
- 다만 internal diagnostics는 나아졌다.
  - `reverse_heading_rescued = 34`
  - delayed continuity gap `28 -> 6`
- 즉 matcher heading/continuity 보정은 일부 먹혔지만, 남은 병목은 route source가 아니라 dense local graph 자체의 geometry / candidate topology 쪽이다.

## 현재 가장 큰 병목

현재 dominant bottleneck은 **route source가 아니라 dense local graph geometry / candidate topology fidelity**다.

근거:
- straight dense는 scoped reverse-heading rescue로 분명히 좋아졌다.
- turn-heavy는 delayed continuity case가 줄었는데도 safety headline은 그대로다.
- direct yaw uncertainty를 다시 파기 전에, dense local graph가 실제 도로 중심선/방향을 얼마나 잘 보존하는지부터 더 봐야 한다.
- 그래서 “route intent가 없어서 못 고른다”보다 “현재 graph edge geometry와 candidate set 자체가 아직 부족하다”가 더 맞다.

## 다음 세션 권고

다음 세션은 **route source가 아니라 graph fidelity / graph semantics**에 집중해야 한다.

우선순위:
1. dense local graph에서 problematic candidate edge를 실제 geometry 기준으로 분류
2. turn-heavy에서 cte가 커지는 구간의 edge topology / crop coverage 확인
3. 그다음에도 필요하면 matcher continuity/heading cost를 한 번 더 손보기
4. direct yaw 후보 재검증은 그 다음

route source는 아직 이르다.

## 아직 미검증인 것

- authoritative direct yaw field
- paused / world-state authoritative field
- authoritative game tick
- trustworthy route source
- HUD calibration 실사용
- control sink write
- Active Mode
