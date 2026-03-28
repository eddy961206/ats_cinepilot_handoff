# Dense Curated Active Demo Design

## Goal

toy gentle-curve active demo 다음 단계로, 실제 ATS local dense graph에서 뽑아낸 짧고 비분기인 corridor 하나만 써서 첫 curated denser-corridor live active demo를 만든다.

## Base State

- session base after consolidation: `main@880cfa5e17da5a9aca8ad304ed350b35dee72021`
- this base already contains PR #6, #7, #8, #9 lineage through PR #10
- straight and toy gentle-curve active demos remain available and must not regress

## Problem Statement

현재 active demo는 toy graph 기반의 직선 / gentle-curve corridor까지만 검증됐다. dense local ATS graph 전체를 그대로 active에 쓰면 candidate ambiguity, branch semantics, edge-direction mismatch 때문에 demo safety cage를 안정적으로 유지하기 어렵다.

이번 세션의 목표는 dense graph research를 더 넓히는 게 아니라:

1. dense local ATS source를 실제로 사용하고,
2. 하지만 corridor는 사람이 읽고 리뷰할 수 있을 정도로 짧고 명시적으로 제한하고,
3. hybrid control path와 strict demo cage를 유지한 채,
4. 첫 curated denser-corridor active demo를 만든다.

## Approaches Considered

### Option A — full dense graph active with stronger matcher tuning

- 장점: 추후 일반화로 바로 이어질 수 있다
- 단점: 이번 milestone이 요구하는 “reviewable한 narrow demo”보다 범위가 너무 넓다
- 결론: 이번 세션 범위 밖

### Option B — dense source에서 corridor subgraph만 추출한 curated demo graph

- 장점:
  - dense local ATS source를 실제로 쓴다
  - graph candidate ambiguity를 corridor asset 자체에서 줄일 수 있다
  - safety cage를 edge sequence contract로 더 명확히 만들 수 있다
  - operator가 한 구간만 준비하면 된다
- 단점:
  - corridor selection과 asset build가 추가로 필요하다
- 결론: 이번 세션 추천안

### Option C — dense graph 전체는 유지하고 config에서 approved_edge_ids만 늘린다

- 장점: 구현량이 적다
- 단점: runtime candidate set는 여전히 dense graph 전체에 노출돼서 active demo safety가 약해진다
- 결론: shadow 실험에는 유용하지만 첫 dense active demo의 기본 경로로는 부적합

## Selected Design

Option B를 채택한다.

구체적으로:

- source graph:
  - `data/maps/cache/ats_usa_region_dense_local_geojson_8km.json`
- selected dense corridor path:
  - `7fc7834877809c8__fwd`
  - `7fc783410280973road0__fwd`
- corridor characteristics:
  - ATS local dense source에서 추출
  - forward-only
  - branch-free chain
  - freeway-class, very gentle curvature, low-speed demo cap
- output curated graph cache:
  - `data/maps/cache/demo_dense_curated_corridor_graph.json`
- output corridor contract:
  - `configs/corridors/demo_dense_curated_corridor.yaml`
- runtime config:
  - `configs/demo_active_dense_corridor.yaml`
- runner:
  - `scripts/run_demo_active_dense_corridor.ps1`

## Corridor Contract

contract는 사람이 읽을 수 있는 YAML로 둔다. 최소 필드는:

- `name`
- `graph_source`
- `alignment_mode`
- `source_cache_path`
- `edge_sequence`
  - edge id
  - travel direction
- `start_edge_id`
- `completion_edge_id`
- `min_progress_m`
- `max_progress_m`
- `max_speed_mps`
- `max_nearest_edge_distance_m`
- `min_match_confidence`
- `min_route_confidence`
- `max_cross_track_error_m`
- `max_heading_error_deg`
- `max_graph_candidate_count`

이 contract는 graph build와 demo cage가 같이 읽는다. config는 이 contract를 참조하고, startup summary에도 corridor name / edge sequence를 찍는다.

## Graph Build Strategy

새 helper는 dense local cache에서 contract의 ordered edge sequence만 추출해서 smaller curated graph cache를 만든다.

요구사항:

- ATS absolute coordinates는 그대로 유지
- edge sequence 순서 보존
- metadata에 source cache, selected edge ids, selected directions, generated_at_utc 기록
- oriented reverse edge가 필요하면 graph build 단계에서 points를 뒤집은 새 edge id를 만든다
- 이번 corridor는 forward-only라 reverse synthetic behavior는 기본으로 두지 않는다

## Safety Cage Strategy

기존 demo cage 철학은 유지한다. dense curated demo는 다음 조건을 모두 만족할 때만 control authority를 준다.

- telemetry healthy
- control sink healthy
- `control.sink=hybrid`
- graph source matches curated dense graph
- alignment mode matches `ats_absolute_identity`
- current edge is within approved sequence
- travel direction matches approved direction
- edge index never moves backward
- preview path exists
- no graph failure
- no discontinuity
- anchor locked
- heading source approved
- candidate count within contract
- nearest-edge distance within contract
- match confidence within contract
- route confidence within contract
- cross-track error within contract
- heading error within contract
- speed below corridor cap
- ATS focus active
- manual override available

위 조건 중 하나라도 깨지면:

- 즉시 neutralize
- keyboard key release
- disengage reason 로그 기록

## Diagnostics

dense curated demo에서 추가로 남길 값:

- `demo_corridor_name`
- `demo_corridor_edge_index`
- `demo_corridor_edge_count`
- `demo_corridor_expected_edge_id`
- `demo_corridor_sequence_ok`
- `demo_corridor_progress_window_ok`
- `graph_source`
- `alignment_mode`
- `steering_abs_max`
- `non_trivial_steering_count`

## Verification Strategy

1. config validation
2. pytest
3. ruff
4. replay smoke
5. gentle-curve baseline reproduction
6. dense curated corridor shadow qualification
7. live telemetry readiness
8. live control readiness
9. first dense curated active demo attempt

## Success Criteria

- dense curated corridor config/runner exists
- shadow qualification stays inside the demo cage long enough to arm
- live active run produces real steering + throttle + brake
- run is clearly on the curated dense graph, not the toy graph
- safety cage dominates behavior and disengages explicitly on failure

## Non-Goals

- general dense local active driving
- route-following
- complex intersections
- CV lane models
- module longitudinal generalization
- broader Active Mode claims
