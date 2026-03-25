# Gentle Curve Active Demo Design

## Goal

기존 직선 corridor constrained active demo를 유지한 채, **시작 직후부터 완만한 곡률이 들어오는 전용 demo corridor**를 추가해서 live closed-loop steering이 실제로 보이게 만든다.

이 세션 목표는 일반 Active Mode나 route-following이 아니다. 좁고 반복 가능한 curved demo를 하나 더 만드는 데만 집중한다.

## Current Context

- usable live control path는 여전히 `hybrid`
  - steering / blinkers: module sink
  - throttle / brake: keyboard sink
- straight demo는 실제로 성공했지만, approved edge `ab`가 100m 직선이라 짧은 active run 안에서는 steering demand가 거의 0이다.
- dense local graph active는 아직 scope 밖이다.
- telemetry / pose / discontinuity / demo cage는 이미 충분히 갖춰져 있다.

## Approaches Considered

### Option A: 기존 toy edge `bc`를 gentle curve demo로 재사용

장점:
- 새 graph cache가 거의 필요 없다
- 현재 toy graph path를 그대로 재활용할 수 있다

단점:
- `bc` 곡률은 `ab` 100m 직선 뒤에 시작한다
- 현재 demo step budget과 low-speed cap으로는 곡률 구간까지 거의 못 간다
- “보이는 closed-loop steering” 목표를 만족시키기 어렵다

### Option B: dense local real graph를 곧바로 curved active demo에 사용

장점:
- 실제 도로 geometry를 더 직접 반영할 수 있다

단점:
- 현재 dominant bottleneck이 dense graph semantics 쪽이라, 이번 세션 scope가 다시 커진다
- branch ambiguity / candidate topology / route absence가 다시 섞인다
- 이번 milestone의 좁고 안전한 demo 철학과 맞지 않는다

### Option C: 시작점부터 바로 완만하게 휘는 dedicated toy gentle-curve corridor를 추가한다

장점:
- 곡률을 demo step budget 안으로 끌어올 수 있다
- graph ambiguity 없이 steering demand를 분리해서 검증할 수 있다
- existing telemetry / control / cage 구조를 그대로 재활용할 수 있다

단점:
- 실제 ATS 도로와 1:1 global alignment는 아니다
- operator가 “비슷한 완만한 커브”에 차를 두어야 해서 운영 절차가 중요하다

## Selected Design

이번 세션은 **Option C**를 선택한다.

핵심 아이디어는 이거다.

1. 새로운 toy graph cache를 추가한다.
2. 그 graph는 branch 없는 forward-only edge 하나만 가진다.
3. edge shape는 시작 후 수 미터 straight + 바로 이어지는 완만한 좌커브로 만든다.
4. 전용 config / runner / log summary를 추가한다.
5. straight demo보다 약간 더 보수적인 speed cap과 curve-safe thresholds를 쓴다.

## Corridor Contract

선택 corridor는 다음 계약을 가진다.

- graph source: `toy_gentle_curve_graph`
- alignment mode: `anchored_local_toy_graph`
- approved edge set: 하나의 curated curve edge만 허용
- travel direction: `forward`
- branch ambiguity: 없음
- candidate count ceiling: `1`
- low speed only

이 corridor는 “곡선 active steering 검증”만 위한 path다. 일반화된 graph path가 아니다.

## Runtime Changes

### 1. Dedicated graph cache

새 cache 예시:

- `data/maps/cache/demo_gentle_curve_graph.json`

shape requirements:

- bootstrap heading lock을 위해 시작부에 짧은 straight segment 유지
- 그 직후 완만한 좌커브
- polyline은 pure pursuit가 충분히 non-zero steering을 낼 정도의 곡률을 가지되, speed cap 2.5~3.0 m/s에서 불안정해지지 않을 정도로 완만해야 함

### 2. Dedicated config

새 config:

- `configs/demo_active_gentle_curve.yaml`

base:
- `configs/live_probe_ats_toy_graph.yaml`

differences from straight demo:
- new cache path
- new `map.source_name`
- new `demo.corridor_name`
- new approved edge IDs
- tighter low-speed cap
- curve용 cross-track / heading / nearest-edge thresholds
- same `hybrid` sink

### 3. Dedicated runner

새 helper:

- `scripts/run_demo_active_gentle_curve.ps1`

flow:
1. override clear
2. config check
3. telemetry readiness
4. control readiness
5. short curved shadow qualification
6. countdown
7. bounded active run
8. log summary print

### 4. Steering observability

현재 recorder에는 `command`와 `status`가 이미 있다.

이번 세션에서 추가할 건:
- steering command min/max/abs max
- non-trivial steering command count
- throttle / brake command counts
- demo guard reason counts
- `safety=NONE` 유지 구간 길이

이건 기존 `scripts/summarize_shadow_log.py`를 일반 demo summary에도 쓸 수 있게 확장하는 쪽이 가장 작다.

## Safety Design

기존 demo cage 철학은 유지하고, curved demo에 맞춰 다음을 더 명시한다.

- graph source exact match
- alignment mode exact match
- approved curved edge only
- preview path required
- anchor locked required
- discontinuity forbidden
- heading source approved set only
- candidate count `<= 1`
- nearest-edge distance hard ceiling
- match confidence floor
- route confidence floor
- cross-track error ceiling
- heading error ceiling
- speed cap hard ceiling
- manual override always immediate

추가 운영 safety:
- keyboard longitudinal path를 쓰므로 ATS foreground focus가 active phase 동안 유지되어야 함
- focus preflight를 runner와 startup summary에 더 명확히 드러낸다
- focus lost는 app-level hard sensing까지는 아직 못 넣더라도, operator-facing 절차와 runner warning은 stronger wording으로 고정한다

## Verification Strategy

1. straight baseline 재현
   - current readiness commands
   - current straight runner
2. curved graph shadow qualification
   - curved config shadow run
   - steering command range가 0에 수렴하지 않는지 확인
3. curved live active attempt
   - bounded active run
   - steering non-trivial count 확인
   - throttle / brake 적용 확인
   - `DEMO_GUARD` / brake assist behavior 확인

## Success Criteria

- 기존 straight demo는 계속 살아 있어야 한다
- new curved demo가 shadow qualification을 통과해야 한다
- live active attempt에서 steering command가 의미 있게 non-zero여야 한다
- throttle / brake도 계속 동작해야 한다
- failure 시 즉시 neutralize / brake assist / override가 먹어야 한다

## Non-Goals

- general route-following
- dense local graph active driving
- 복잡한 intersection handling
- module longitudinal 일반화
- CV / ML / lane model

## Expected Next Milestone

이 gentle-curve demo가 성공하면 다음 milestone은 **curated denser corridor active demo**가 맞다.

실패하면 다음 milestone은 여전히 same curved corridor 안에서:

- graph shape
- speed cap
- steering thresholds
- focus/operator procedure

를 더 다듬는 것이다.
