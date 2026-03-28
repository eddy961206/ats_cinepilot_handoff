# Implementation Status

## 2026-03-29 실제 상태

### 이번 세션 base 상태

- 이번 작업 base는 `main@6eb557371a4806595f4e4fbfa0c28356367bcfd4`였다.
- `main`에는 curated dense active demo lineage가 이미 들어 있었고 추가 consolidation은 필요 없었다.

## 지금 실제로 검증된 것

### telemetry / pose

- `SCSTelemetrySharedv2_ats` live ingest 동작
- absolute pose 계약 유지
  - `285:f64 -> world_x`
  - `293:f64 -> world_y`
  - `301:f64 -> world_z`
- discontinuity detection / anchor reset 동작

### control path

- `scs-sdk-controller` steering / blinker write는 실제로 보였다
- module throttle / brake는 아직 실사용 경로가 아니다
- keyboard `W/S`는 실제로 먹는다
- 현재 usable control path는 계속 `hybrid`
  - steering / blinkers: module sink
  - throttle / brake: keyboard sink

### constrained active demos

- straight constrained live active demo 존재
  - config: `configs/demo_active_corridor.yaml`
  - helper: `scripts/run_demo_active_corridor.ps1`
- gentle-curve constrained live active demo 존재
  - config: `configs/demo_active_gentle_curve.yaml`
  - helper: `scripts/run_demo_active_gentle_curve.ps1`
- curated denser-corridor constrained live active demo 존재
  - config: `configs/demo_active_dense_corridor.yaml`
  - helper: `scripts/run_demo_active_dense_corridor.ps1`

### 이번 세션에서 새로 실제로 된 것

- durable ops / handoff harness 추가
  - `docs/ops/CURRENT_STATE.md`
  - `docs/ops/ROADMAP.md`
  - `docs/ops/DECISIONS.md`
  - `docs/ops/EXPERIMENT_LOG.md`
  - `docs/ops/FAILED_ATTEMPTS.md`
  - `docs/ops/CHECKLISTS/*`
  - `docs/ops/NEXT_AGENT_BRIEF.md`
  - `state/latest_session_state.json`
  - `scripts/update_session_handoff.py`
- CV observer v1 추가
  - lane observer: classical ROI/Hough
  - vehicle observer: pretrained OpenCV DNN
  - barrier / road-edge: 아직 미구현
- human-visible overlay / artifact 저장 추가
  - annotated frames
  - annotated MP4
  - CV summary JSONL
- dense demo에 CV observer/guard를 보수적으로 얹는 경로 추가
  - observer-only config: `configs/cv_observer_dense_corridor.yaml`
  - active+CV config: `configs/demo_active_dense_corridor_with_cv.yaml`
  - observer helper: `scripts/run_cv_observer_dense_corridor.ps1`
  - active+CV helper: `scripts/run_demo_active_dense_corridor_with_cv.ps1`

## live CV observer 실제 결과

command:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_cv_observer_dense_corridor.ps1 -Steps 80
```

actual summary:

- `frames=80`
- `lane_detected=80`
- `lane_conf=[1.000, 1.000]`
- `lead_detected=0`
- `guard_reasons={none: 80}`

artifact paths:

- `data/artifacts/cv/observer_dense_corridor/observer_overlay.mp4`
- `data/artifacts/cv/observer_dense_corridor/frame_00001.jpg`
- `data/logs/cv_observer_dense_corridor.cv.jsonl`

해석:

- lane overlay는 live ATS capture에서 실제로 생성됐다
- 사람은 overlay window로 바로 볼 수 있고, 저장 산출물도 남는다
- observer-only run에서는 앞차가 live로 안 잡혀서 vehicle evidence는 아직 제한적이다

## dense curated active demo with CV 실제 결과

command:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_demo_active_dense_corridor_with_cv.ps1 -ShadowSteps 8 -ActiveSteps 80 -ActiveCountdownSeconds 3
```

actual summary:

- `steps=88`
- `safety={MATCH_LOST: 17, ROUTE_CONFIDENCE_LOW: 2, DEMO_GUARD: 21, NONE: 48}`
- `match=[0.700, 1.000]`
- `route=[0.480, 0.700]`
- `cte_max=0.039`
- `cand=[1, 1]`
- `steering_abs_max=0.300`
- `non_trivial_steering_count=20`
- `throttle_command_count=34`
- `brake_command_count=51`
- `lane_detected=88`
- `lead_detected=0`

해석:

- CV layer를 켠 상태에서도 dense curated active demo는 실제로 돌았다
- planner/control primary path는 그대로 telemetry + graph + hybrid sink다
- CV는 overlay/artifact/guard layer로만 동작했다
- 이번 run에서는 lead-vehicle risk 상황이 없어서 CV guard trigger는 없었다

### post-review short rerun

command:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_demo_active_dense_corridor_with_cv.ps1 -ShadowSteps 4 -ActiveSteps 40 -ActiveCountdownSeconds 3
```

actual summary:

- `steps=44`
- `safety={MATCH_LOST: 44}`
- `cte_max=7.109`
- `lane_detected=44`
- `lead_detected=2`
- `lead_conf_max=0.567`

해석:

- review fix 뒤 normal CV path는 여전히 실행됐다
- dense active repeatability는 여전히 흔들린다
- 대신 live vehicle detector가 ATS 장면에서 일부 positive를 냈다는 증거는 생겼다
- 아직 current guard threshold `0.60`을 넘는 confident lead target은 못 얻었다

## 현재 선택 계약

### observer-only CV run

- graph: `curated_dense_local_corridor_graph`
- alignment: `ats_absolute_identity`
- control sink: `noop`
- config: `configs/cv_observer_dense_corridor.yaml`

### dense curated active + CV

- graph: `curated_dense_local_corridor_graph`
- alignment: `ats_absolute_identity`
- runtime contract: `data/runtime/demo_dense_curated_corridor.runtime.yaml`
- runtime graph: `data/maps/cache/demo_dense_curated_corridor.runtime.json`
- sink: `hybrid`
- config: `configs/demo_active_dense_corridor_with_cv.yaml`
- CV guard mode: `disengage_only`
- lane guard default: off
- lead vehicle guard default: on

## demo cage + CV guard 조건

기존 active control 허용 조건은 그대로 유지된다.

추가 CV status fields:

- `cv_enabled`
- `lane_detected`
- `lane_confidence`
- `lane_offset_estimate_px`
- `lead_vehicle_detected`
- `lead_vehicle_confidence`
- `visual_barrier_risk`
- `cv_guard_reason`
- `cv_overlay_path`

CV가 이번 세션에서 할 수 있는 것:

- lane overlay / confidence
- vehicle bounding box / lead candidate
- disengage-only visual guard
- artifact saving / explainability

CV가 이번 세션에서 하지 않는 것:

- end-to-end steering
- planner replacement
- route following
- barrier-safe driving claims

## 현재 한계

- module longitudinal는 아직 실사용 계약이 아니다
- keyboard longitudinal는 ATS foreground focus가 필요하다
- dense demo corridor는 runtime fit된 one-chain corridor 하나뿐이다
- barrier / road-edge perception은 아직 없다
- live vehicle detection positive evidence는 일부만 확보됐다
- lead vehicle guard trigger evidence는 아직 없다
- lane guard는 live ATS fixture acceptance가 아직 없어서 기본으로 안 켠다
- dense-local general active driving은 아직 아니다
- route-aware active는 아직 아니다

## 현재 결론

이번 milestone은 **CV observer + overlay + durable handoff harness가 올라간 constrained dense active demo**다.

정확한 의미:

- lane overlay는 live ATS에서 실제로 보였다
- annotated video / frame / JSONL artifact가 실제로 저장된다
- dense active demo에 CV를 켠 상태로 실제로 돌릴 수 있다
- CV는 planner를 대체하지 않고 observer/guard로만 붙었다
- future agent는 `docs/ops`와 `state/latest_session_state.json`만 읽고 이어받을 수 있다

아직 의미하지 않는 것:

- visual route following
- CV-only driving
- barrier-safe autonomy
- general Active Mode

## 다음 dominant bottleneck

지금 가장 큰 병목은 `route source`가 아니라:

1. curated corridor repeatability
2. demo-only longitudinal shaping
3. live vehicle / barrier visual evidence 부족

즉 다음 단계는 CV-first generalization이 아니라 **curated multi-edge dense corridor + richer live visual risk evidence**가 맞다.

## 다음 추천 작업

1. live traffic가 있는 장면에서 confident lead target / guard trigger evidence를 추가 수집
2. barrier/road-edge observer는 필요하면 그 다음에 narrow하게 추가
3. curated multi-edge dense corridor로 확장
4. route-aware demo는 아직 미루기
