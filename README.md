# ATS CinePilot

ATS에서 **첫 gentle-curve constrained live active demo**까지 bring-up한 프로젝트야.

이 프로젝트의 철학은 그대로다.

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

현재 gentle-curve demo path:

- config: `configs/demo_active_gentle_curve.yaml`
- helper: `scripts/run_demo_active_gentle_curve.ps1`
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

gentle-curve demo에선 keyboard longitudinal PWM을 추가로 쓴다.

- `control.keyboard.longitudinal_pwm_period_s=0.25`

## live active demo에서 실제로 확인된 것

### straight baseline

직선 corridor baseline은 유지된다.

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_demo_active_corridor.ps1 -ShadowSteps 20 -ActiveSteps 80 -ActiveCountdownSeconds 8
```

### gentle-curve constrained demo

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_demo_active_gentle_curve.ps1 -ShadowSteps 25 -ActiveSteps 120 -ActiveCountdownSeconds 8
```

verified run summary:

- `steps=145`
- `safety={NONE: 111, MATCH_LOST: 9, DEMO_GUARD: 24, ROUTE_CONFIDENCE_LOW: 1}`
- `first_MATCH_LOST=92`
- `steering_abs_max=0.209`
- `non_trivial_steering_count=32`
- `throttle_command_count=126`
- `brake_command_count=18`

즉:

- 곡선 구간에서 실제 non-zero steering이 걸렸다
- throttle과 brake도 같은 run 안에서 적용됐다
- safety cage는 조건이 깨지면 실제로 disengage했다

중요:

- 이건 toy gentle curve 하나에만 맞춘 demo다
- dense-local general active driving이 아니다
- route-following이 아니다
- general autopilot capability claim이 아니다

## 데모 제약

이 demo는 아래 조건에서만 의미가 있다.

- one corridor only
- toy graph only
- forward only
- low speed only
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
.\.venv\Scripts\ats-cinepilot check-config --config configs\demo_active_gentle_curve.yaml
```

### live telemetry probe

```powershell
.\.venv\Scripts\python scripts\inspect_telemetry.py --config configs\demo_active_gentle_curve.yaml --frames 3 --require-ready
```

### live control probe

```powershell
.\.venv\Scripts\python scripts\inspect_controls.py --config configs\demo_active_gentle_curve.yaml --dry-run --require-ready
```

### gentle-curve constrained active demo

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_demo_active_gentle_curve.ps1 -ShadowSteps 25 -ActiveSteps 120 -ActiveCountdownSeconds 8
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
- approved edge
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
- dense local graph 기반 constrained active corridor
- HUD calibration 실사용
- general Active Mode
- route-aware autonomy 일반화

## 다음 권장 단계

1. gentle-curve demo를 human-run으로 반복 재현
2. demo-only longitudinal shaping을 조금 더 다듬기
3. 그 다음에만 curated denser corridor 1개로 확장
4. route-following이나 dense-local general active는 아직 미루기

자세한 상태:

- `docs/IMPLEMENTATION_STATUS.md`
- `docs/RUNBOOK.md`
- `docs/LOCAL_SETUP.md`
- `docs/SHARED_MEMORY_V2_DESIGN.md`
