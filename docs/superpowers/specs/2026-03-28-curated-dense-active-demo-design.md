# Curated Dense Corridor Active Demo Design

## Goal

기존 toy gentle-curve active demo를 유지한 채, **실제 ATS local dense graph에서 잘라낸 짧은 curated corridor** 하나를 추가해서 첫 denser-corridor live active demo를 만든다.

이번 세션 목표는 general Active Mode나 route-following이 아니다. dense local graph 전체를 풀지 않고, 이미 export된 local dense graph에서 **분기 없는 짧은 corridor만 안전하게 재사용**하는 데 집중한다.

## Current Context

- `main@880cfa5`가 이제 PR #6 / #7 / #8 / #9 lineage까지 포함한다.
- usable live control path는 여전히 `hybrid`
  - steering / blinkers: module sink
  - throttle / brake: keyboard sink
- straight constrained demo와 toy gentle-curve constrained demo는 이미 존재한다.
- dense local graph는 shadow / matcher 연구에는 충분했지만, 전체 graph 그대로는 active demo용 safety cage가 너무 넓다.

## Approaches Considered

### Option A: dense local graph 전체를 그대로 active demo에 사용

장점:
- 새 graph artifact가 필요 없다
- 현재 live probe config를 바로 재활용할 수 있다

단점:
- candidate ambiguity와 branch topology가 그대로 남는다
- 이번 milestone이 다시 “general dense active”로 커진다
- strict demo cage 철학과 맞지 않는다

### Option B: dense local graph에서 approved edge sequence만 추출한 curated subgraph를 만든다

장점:
- geometry는 toy보다 현실적이다
- branch ambiguity를 artifact 수준에서 제거할 수 있다
- active demo safety cage가 명확해진다
- operator에게 corridor start만 알려주면 된다

단점:
- 새 corridor export artifact가 하나 더 필요하다
- explicit sequence contract를 코드와 문서에 같이 유지해야 한다

### Option C: dense graph를 쓰지 않고 toy graph를 하나 더 만든다

장점:
- 구현이 가장 쉽다

단점:
- 이번 milestone 목표인 “denser corridor”를 충족하지 못한다
- PR #9 대비 실제 진전이 약하다

## Selected Design

이번 세션은 **Option B**를 선택한다.

핵심 아이디어는 이거다.

1. 기존 `ats_usa_region_dense_local_geojson_8km.json`에서 이미 live area 근처에 있는 짧은 unique traversal chain 하나를 고른다.
2. 그 chain을 **travel-direction이 고정된 oriented edge sequence**로 잘라낸 dedicated graph cache를 만든다.
3. active demo는 dense local graph 전체가 아니라 이 curated dense subgraph에서만 arm되게 만든다.
4. corridor contract는 사람이 읽을 수 있는 YAML/JSON artifact로 따로 둔다.
5. demo cage는 edge set뿐 아니라 **edge order / progress / corridor start state**까지 검사한다.

## Selected Corridor

현재 가장 안전한 후보는 이전 live probe area와 같은 좌표권에 있는 이 sequence다.

- source graph: `data/maps/cache/ats_usa_region_dense_local_geojson_8km.json`
- source traversals:
  - `62b6432ed230ae6__fwd / forward`
  - `62b643239430ae8road1__fwd / reverse`
  - `62b643214b30a31__fwd / forward`
  - `62b6432a2430a32road0__fwd / forward`
  - `62b643269a30a33__fwd / forward`
  - `62b643283030e72road1__fwd / reverse`

이 sequence의 성질:

- local live probe 좌표권과 가깝다
- 각 state에서 continuation이 사실상 하나다
- cumulative heading change는 작지만 0은 아니다
- total corridor length는 약 `280m`
- start/end world coordinates가 명확하다

## Corridor Contract

새 corridor contract artifact는 최소한 다음을 가진다.

- `corridor_name`
- `graph_source`
- `alignment_mode`
- `graph_cache_path`
- `source_cache_path`
- `ordered_edges`
  - runtime edge ID
  - source edge ID
  - source travel direction
  - start/end world coordinates
- `start_edge_id`
- `end_edge_id`
- `max_speed_mps`
- `min_match_confidence`
- `min_route_confidence`
- `max_cross_track_error_m`
- `max_heading_error_deg`
- `max_nearest_edge_distance_m`
- `max_graph_candidate_count`

중요한 점은 이 contract가 “general planner가 알아서 잘 해주길 기대”하는 게 아니라, **이번 demo에서 허용되는 corridor semantics를 명시적으로 고정**한다는 거다.

## Runtime Changes

### 1. Dedicated dense corridor graph cache

새 cache:

- `data/maps/cache/demo_dense_curated_corridor_graph.json`

이 graph는 source dense graph의 6개 traversal만 포함하고, runtime에선 전부 `forward` travel만 쓰도록 oriented points로 저장한다.

즉, source graph에선 reverse traversal이 필요했던 segment도 curated graph에선 새 edge로 정방향화된다.

### 2. Dedicated corridor contract artifact

새 artifact:

- `configs/corridors/demo_dense_curated_corridor.yaml`

이 파일은 graph cache와 1:1로 대응하고, runtime safety cage / startup summary / operator docs가 같은 계약을 공유하게 만든다.

### 3. Dedicated config and runner

새 config:

- `configs/demo_active_dense_corridor.yaml`

새 helper:

- `scripts/run_demo_active_dense_corridor.ps1`

base는 gentle-curve demo와 비슷하지만 다음이 다르다.

- graph source / cache path
- corridor contract path
- approved edge sequence
- speed cap
- readiness wording
- log path

### 4. Corridor-aware demo safety

기존 `DemoSafetyCage`는 edge set membership까지만 본다. 이번 세션에선 다음을 추가한다.

- ordered corridor edge sequence
- current edge index 추적
- corridor regression / skip 검출
- outside approved sequence 즉시 disengage
- progress reset / start edge re-entry semantics

이 로직은 general route following이 아니라 demo-only corridor tracker다.

### 5. Startup / recorder diagnostics

dense curated demo에선 다음을 더 명시한다.

- corridor contract name
- corridor edge index / total edge count
- corridor sequence valid 여부
- corridor start satisfied 여부
- demo graph source / alignment

## Verification Strategy

1. gentle-curve baseline 재현
2. dense corridor config readiness
3. dense corridor shadow qualification
4. dense corridor live active attempt
5. log summary로 아래 확인
   - `steering_abs_max`
   - `non_trivial_steering_count`
   - `safety_counts`
   - `first disengage step`
   - `candidate_count range`
   - `approved edge sequence respected`

## Success Criteria

- gentle-curve baseline이 계속 재현돼야 한다
- dense curated corridor shadow qualification이 통과해야 한다
- dense curated corridor active demo에서 실제 steering / throttle / brake가 모두 기록돼야 한다
- active authority는 corridor contract가 만족될 때만 살아야 한다
- 조건이 깨지면 즉시 neutralize / key release / guard reason 기록이 나와야 한다

## Non-Goals

- dense local graph 전체 active driving
- general route following
- complex intersections
- HUD route source
- module longitudinal 일반화
- CV / ML

## Expected Next Milestone

이 curated dense corridor demo가 성공하면 다음 milestone은 둘 중 하나다.

- curated dense multi-edge corridor를 한 단계 더 늘리는 것
- 혹은 같은 curated corridor에 **아주 제한된 route-aware branch intent**를 붙이는 것

이번 세션에서 dense curated demo가 불안정하면, 다음 세션도 여전히 corridor contract / graph artifact / demo cage를 다듬는 쪽이 맞다.
