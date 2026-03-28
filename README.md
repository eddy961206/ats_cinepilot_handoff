# ATS CinePilot

ATS에서 **첫 curated denser-corridor constrained live active demo**까지 bring-up한 프로젝트야.

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

현재 dense curated demo path:

- config: `configs/demo_active_dense_corridor.yaml`
- helper: `scripts/run_demo_active_dense_corridor.ps1`
- override kill-switch: `scripts/demo_override_on.ps1`

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

즉:

- dense curated corridor에서도 real steering이 걸렸다
- throttle과 brake도 같은 run 안에서 적용됐다
- review fix 이후에도 runtime fit이 `dense_seg_04` 단일 edge corridor로 trim된 상태에서 candidate count `1`을 유지했다
- safety cage는 bootstrap / arming / armed / brake assist를 실제로 수행했다

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
- ATS 창 focus 유지
- operator takeover 가능

## 바로 돌리는 명령

### setup

```powershell
.\scripts\setup_venv.ps1
```

### config check

```powershell
.\.venv\Scripts\ats-cinepilot check-config --config configs\demo_active_dense_corridor.yaml
```

### live telemetry probe

```powershell
.\.venv\Scripts\python scripts\inspect_telemetry.py --config configs\demo_active_dense_corridor.yaml --frames 3 --require-ready
```

### live control probe

```powershell
.\.venv\Scripts\python scripts\inspect_controls.py --config configs\demo_active_dense_corridor.yaml --dry-run --require-ready
```

### dense curated constrained active demo

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_demo_active_dense_corridor.ps1 -ShadowSteps 12 -ActiveSteps 140 -ActiveCountdownSeconds 3
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

## 아직 안 된 것

- module longitudinal write
- direct yaw 채택
- dense-local general active driving
- route-aware active demo
- HUD calibration 실사용
- general Active Mode

## 다음 권장 단계

1. dense curated corridor demo를 반복 재현
2. demo-only longitudinal shaping을 더 다듬기
3. 그 다음에만 curated multi-edge corridor로 확장
4. route-aware demo는 아직 미루기

자세한 상태:

- `docs/IMPLEMENTATION_STATUS.md`
- `docs/RUNBOOK.md`
- `docs/LOCAL_SETUP.md`
- `docs/SHARED_MEMORY_V2_DESIGN.md`
