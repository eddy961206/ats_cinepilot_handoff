# ATS CinePilot

ATS에서 **아주 좁게 제한된 live active demo**까지 bring-up한 프로젝트야.

이 프로젝트의 현재 철학은 그대로다.

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
- dense graph matcher diagnostics / direction rescue 경로 존재
- constrained live active demo 경로 존재
  - config: `configs/demo_active_corridor.yaml`
  - helper: `scripts/run_demo_active_corridor.ps1`
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

이건 타협이지만, 이번 milestone 목표인 **첫 constrained live active demo**에는 맞다.

## live active demo에서 실제로 확인된 것

### micro-probe

같은 프로세스에서 telemetry와 함께 hybrid sink를 찍었고:

- throttle 구간: `3.611 -> 13.777 m/s`
- brake 구간: `15.340 -> 0.000 m/s`

즉 longitudinal write는 실제 ATS live session에서 먹었다.

### short active demo attempt

`scripts/run_demo_active_corridor.ps1 -ShadowSteps 20 -ActiveSteps 80 -ActiveCountdownSeconds 8`

이 run에서:

- bootstrap 이후 `0.00 -> 2.54 m/s`
- armed 이후 `2.51 -> 4.10 m/s`
- speed cap exceeded 후 brake assist로 `5.34 -> 1.95 m/s`

즉 active loop 안에서 throttle과 brake는 실제로 적용됐다.

중요:

- chosen corridor가 직선 toy segment라서 active run 중 steering command는 거의 0 근처였다
- steering write path 자체는 module pulse로 따로 visual 확인했다
- 그래서 이걸 “복잡한 조향까지 검증된 일반 Active Mode”라고 부르면 안 된다

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

즉 지금 milestone은 **active autopilot 일반화**가 아니라 **한 corridor에서의 live demo**다.

## 바로 돌리는 명령

### setup

```powershell
.\scripts\setup_venv.ps1
```

### config check

```powershell
.\.venv\Scripts\ats-cinepilot check-config --config configs\demo_active_corridor.yaml
```

### live telemetry probe

```powershell
.\.venv\Scripts\python scripts\inspect_telemetry.py --config configs\demo_active_corridor.yaml --frames 3 --require-ready
```

### live control probe

```powershell
.\.venv\Scripts\python scripts\inspect_controls.py --config configs\demo_active_corridor.yaml --dry-run --require-ready
```

### constrained active demo

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_demo_active_corridor.ps1 -ShadowSteps 20 -ActiveSteps 80 -ActiveCountdownSeconds 8
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
- dense local graph 기반 constrained route-following
- HUD calibration 실사용
- general Active Mode
- route-aware autonomy 일반화

## 다음 권장 단계

1. human-run으로 demo를 한 번 더 재현
2. focus requirement를 운영 절차로 고정
3. module longitudinal failure를 별도 분리 조사
4. 그 다음에만 corridor를 조금 넓히기

자세한 상태:

- `docs/IMPLEMENTATION_STATUS.md`
- `docs/RUNBOOK.md`
- `docs/LOCAL_SETUP.md`
- `docs/SHARED_MEMORY_V2_DESIGN.md`
