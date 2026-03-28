# ATS CinePilot

ATS에서 **curated denser-corridor constrained live active demo + CV observer overlay**까지 bring-up한 프로젝트야.

이 프로젝트 철학은 그대로다.

- CV-first로 가지 않는다
- telemetry + graph + rule-based controller를 우선한다
- 지금 목표는 general autopilot이 아니라 **reviewable한 constrained demo**다

## 현재 실제로 된 것

- replay shadow mode 동작
- `SCSTelemetrySharedv2_ats` live ingest 동작
- absolute pose 계약 사용 중
  - `285:f64 -> world_x`
  - `293:f64 -> world_y`
  - `301:f64 -> world_z`
- discontinuity detection / anchor reset 동작
- straight constrained live active demo 경로 존재
- gentle-curve constrained live active demo 경로 존재
- curated denser-corridor constrained live active demo 경로 존재
- live CV observer overlay 경로 존재
- dense curated active demo에 CV observer/guard를 얹는 경로 존재
- durable in-repo handoff/ops harness 존재

현재 dense curated demo path:

- config: `configs/demo_active_dense_corridor.yaml`
- helper: `scripts/run_demo_active_dense_corridor.ps1`
- override kill-switch: `scripts/demo_override_on.ps1`

현재 CV path:

- observer-only config: `configs/cv_observer_dense_corridor.yaml`
- observer helper: `scripts/run_cv_observer_dense_corridor.ps1`
- active+CV config: `configs/demo_active_dense_corridor_with_cv.yaml`
- active+CV helper: `scripts/run_demo_active_dense_corridor_with_cv.ps1`

## 현재 control path 결론

실측 결과는 이거야.

- module steering: 됨
- module blinker: 됨
- module throttle / brake: 아직 안 됨
- keyboard `W/S`: 됨

그래서 현재 demo는 `hybrid` sink를 쓴다.

- steering / blinkers: `scs-sdk-controller` module sink
- throttle / brake: Windows keyboard injection

## dense curated demo가 실제로 의미하는 것

이 demo는 general dense-local driving이 아니야.

- checked-in source corridor chain은 고정이다
- helper가 run 시작 전에 현재 truck 위치를 그 chain에 runtime fit한다
- exported runtime graph는 그 run에서만 쓰는 translated corridor다
- safety cage는 approved edge sequence / direction / pose source / heading source를 강하게 검사한다

## CV layer가 실제로 의미하는 것

이 프로젝트는 CV-first로 바뀐 게 아니야.

- primary path는 여전히 telemetry + graph + rule-based controller다
- CV는 이번 세션에서 observer / overlay / disengage-only guard로만 들어갔다
- lane overlay와 vehicle boxes를 사람에게 보여준다
- dense demo run 중에도 artifact를 남긴다
- lead vehicle guard는 보수적으로 disengage-only다

## live active demo에서 실제로 확인된 것

### straight baseline

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_demo_active_corridor.ps1 -ShadowSteps 20 -ActiveSteps 80 -ActiveCountdownSeconds 8
```

### gentle-curve constrained demo

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_demo_active_gentle_curve.ps1 -ShadowSteps 25 -ActiveSteps 120 -ActiveCountdownSeconds 8
```

### dense curated corridor constrained demo

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_demo_active_dense_corridor.ps1 -ShadowSteps 12 -ActiveSteps 140 -ActiveCountdownSeconds 3
```

### observer-only CV overlay

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_cv_observer_dense_corridor.ps1 -Steps 80
```

### dense curated corridor constrained demo with CV

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_demo_active_dense_corridor_with_cv.ps1 -ShadowSteps 8 -ActiveSteps 80 -ActiveCountdownSeconds 3
```

verified dense run summary:

- `steps=152`
- `safety={MATCH_LOST: 31, ROUTE_CONFIDENCE_LOW: 4, DEMO_GUARD: 25, NONE: 92}`
- `match=[0.696, 1.000]`
- `route=[0.487, 0.700]`
- `cte_max=0.030`
- `steering_abs_max=0.300`
- `non_trivial_steering_count=35`
- `throttle_command_count=31`
- `brake_command_count=121`

verified observer-only CV summary:

- `frames=80`
- `lane_detected=80`
- `lane_conf=[1.000, 1.000]`
- `lead_detected=0`

verified dense+CV run summary:

- `steps=88`
- `safety={MATCH_LOST: 17, ROUTE_CONFIDENCE_LOW: 2, DEMO_GUARD: 21, NONE: 48}`
- `match=[0.700, 1.000]`
- `route=[0.480, 0.700]`
- `cte_max=0.039`
- `steering_abs_max=0.300`
- `non_trivial_steering_count=20`
- `lane_detected=88`
- `lead_detected=0`

중요:

- 이건 curated corridor 하나에만 맞춘 demo다
- dense-local general active driving이 아니다
- route-following이 아니다
- general autopilot capability claim이 아니다

## 데모 제약

이 demo는 아래 조건에서만 의미가 있다.

- one curated corridor only
- forward only
- low speed only
- runtime fit된 translated graph only
- route ambiguity 없음
- discontinuity 없음
- ATS 창 maximized 또는 full-screen 권장
- ATS 창 focus 유지
- operator takeover 가능

observer-only CV run은 control이 `noop`라서 ATS focus requirement가 없다.

## 바로 돌리는 명령

### setup

```powershell
.\scripts\setup_venv.ps1
```

### config check

```powershell
.\.venv\Scripts\ats-cinepilot check-config --config configs\demo_active_dense_corridor.yaml
.\.venv\Scripts\ats-cinepilot check-config --config configs\cv_observer_dense_corridor.yaml
.\.venv\Scripts\ats-cinepilot check-config --config configs\demo_active_dense_corridor_with_cv.yaml
```

### live telemetry probe

```powershell
.\.venv\Scripts\python scripts\inspect_telemetry.py --config configs\demo_active_dense_corridor.yaml --frames 3 --require-ready
```

### live control probe

```powershell
.\.venv\Scripts\python scripts\inspect_controls.py --config configs\demo_active_dense_corridor.yaml --dry-run --require-ready
```

### CV models

```powershell
.\.venv\Scripts\python scripts\download_cv_models.py --config configs\cv_observer_dense_corridor.yaml
```

### observer-only CV run

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_cv_observer_dense_corridor.ps1 -Steps 80
```

### dense curated constrained active demo

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_demo_active_dense_corridor.ps1 -ShadowSteps 12 -ActiveSteps 140 -ActiveCountdownSeconds 3
```

### dense curated constrained active demo with CV

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_demo_active_dense_corridor_with_cv.ps1 -ShadowSteps 8 -ActiveSteps 80 -ActiveCountdownSeconds 3
```

## safety

수동 disengage:

1. ATS에서 바로 브레이크 / 조향 takeover
2. `Esc`
3. `Ctrl+C`
4. 다른 터미널에서 `scripts\demo_override_on.ps1`

demo cage는 아래가 깨지면 즉시 neutralize한다.

- telemetry freshness
- approved graph / alignment
- approved edge sequence
- match confidence
- route confidence
- cross-track error
- heading error
- candidate count
- speed cap
- discontinuity
- manual override

speed cap exceeded일 때만 brake-only assist는 허용한다.

CV가 켜진 config에서는 아래 status도 같이 남긴다.

- `lane_detected`
- `lane_confidence`
- `lane_offset_estimate_px`
- `lead_vehicle_detected`
- `lead_vehicle_confidence`
- `visual_barrier_risk`
- `cv_guard_reason`
- `cv_overlay_path`

## 아직 안 된 것

- module longitudinal write
- direct yaw 채택
- dense-local general active driving
- route-aware active demo
- HUD calibration 실사용
- general Active Mode
- barrier / road-edge perception
- live vehicle-detection positive evidence 충분히 확보

## 다음 권장 단계

1. traffic가 있는 장면에서 vehicle detector / lead guard evidence 추가 확보
2. dense curated corridor demo를 반복 재현
3. demo-only longitudinal shaping을 더 다듬기
4. 그 다음에만 curated multi-edge corridor로 확장

자세한 상태:

- `docs/IMPLEMENTATION_STATUS.md`
- `docs/RUNBOOK.md`
- `docs/LOCAL_SETUP.md`
- `docs/SHARED_MEMORY_V2_DESIGN.md`
- `docs/ops/NEXT_AGENT_BRIEF.md`
- `docs/ops/CURRENT_STATE.md`
