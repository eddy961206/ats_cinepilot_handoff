# Runbook

## 현재 목표

지금 운영 목표는 **첫 gentle-curve constrained live active demo 반복 재현**이야.

즉:

- telemetry는 live
- control은 live
- corridor는 하나
- 곡률은 아주 완만하게
- speed는 낮게
- safety cage는 빡세게

general autopilot 운영 문서가 아니다.

## base 상태 확인

작업 시작 전에 먼저 확인해.

- `main`이 PR #6 / #7 / #8 lineage까지 포함하는지
- 아니라면 stale `main`에서 새 작업 시작하지 않는지
- 필요한 경우 `codex/real-ats-world-graph-alignment` lineage를 base로 쓰는지

## 현재 선택 demo path

### straight baseline

- config: `configs/demo_active_corridor.yaml`
- helper: `scripts/run_demo_active_corridor.ps1`

### gentle curve demo

- config: `configs/demo_active_gentle_curve.yaml`
- helper: `scripts/run_demo_active_gentle_curve.ps1`
- graph: `toy_gentle_curve_graph`
- alignment: `anchored_local_toy_graph`
- approved edge: `curve_ab`
- speed cap: `3.0 m/s`

### hybrid sink 의미

- steering / blinkers -> module sink
- throttle / brake -> keyboard sink

gentle-curve demo에선 keyboard longitudinal PWM을 쓴다.

- `control.keyboard.longitudinal_pwm_period_s=0.25`

## preflight

### 1. 환경

```powershell
.\scripts\setup_venv.ps1
```

### 2. config check

```powershell
.\.venv\Scripts\ats-cinepilot check-config --config configs\demo_active_gentle_curve.yaml
```

### 3. telemetry probe

```powershell
.\.venv\Scripts\python scripts\inspect_telemetry.py --config configs\demo_active_gentle_curve.yaml --frames 3 --require-ready
```

성공 기준:

- `telemetry status: telemetry ready`
- `SCSTelemetrySharedv2_ats` visible
- decode OK

### 4. control probe

```powershell
.\.venv\Scripts\python scripts\inspect_controls.py --config configs\demo_active_gentle_curve.yaml --dry-run --require-ready
```

성공 기준:

- module path ready
- keyboard path ready
- hybrid status ready
- `keyboard longitudinal pwm: enabled period_s=0.25`

## operator preconditions

반드시 맞춰.

- ATS running
- drivable state
- engine on
- forward gear
- parking brake 해제
- selected gentle curve 초입
- ATS 창 foreground 유지
- operator 손은 즉시 takeover 가능

## straight baseline 재현

필요할 때 baseline으로 먼저 확인해.

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_demo_active_corridor.ps1 -ShadowSteps 20 -ActiveSteps 80 -ActiveCountdownSeconds 8
```

## gentle-curve active demo

실행:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_demo_active_gentle_curve.ps1 -ShadowSteps 25 -ActiveSteps 120 -ActiveCountdownSeconds 8
```

helper가 하는 일:

1. override clear
2. config check
3. telemetry probe
4. control probe
5. shadow qualification
6. countdown
7. active run
8. log summary 출력

## 현재 실제 gentle-curve 결과

이번 세션의 verified run:

```text
steps=145
safety={NONE: 111, MATCH_LOST: 9, DEMO_GUARD: 24, ROUTE_CONFIDENCE_LOW: 1}
first_MATCH_LOST=92
steering_abs_max=0.209
non_trivial_steering_count=32
throttle_command_count=126
brake_command_count=18
demo_guard_reasons={bootstrap: 91, heading_source_unapproved: 4, arming: 11, armed: 20, speed_cap_exceeded: 19}
```

해석:

- 곡선 구간에서 non-zero steering이 실제로 발생했다
- throttle / brake도 같은 run 안에서 실제로 적용됐다
- 다만 `speed_cap_exceeded`는 아직 주요 disengage 원인이다

## manual disengage

아래 중 하나면 된다.

1. 브레이크 / 조향 직접 takeover
2. `Esc`
3. `Ctrl+C`
4. 다른 터미널에서:

```powershell
scripts\demo_override_on.ps1
```

해제:

```powershell
scripts\demo_override_off.ps1
```

## failure 해석

### telemetry ready가 아님

- ATS not running
- plugin missing
- mapping missing
- unsupported layout

### control path ready가 아님

- plugin DLL missing
- Python module missing
- field mapping mismatch
- keyboard sink platform issue

### active run이 안 움직임

먼저 이 셋부터 봐.

1. ATS 창이 foreground였는지
2. drivable state였는지
3. override flag가 켜져 있지 않은지

### curve demo가 바로 끊김

먼저 이 네 개부터 봐.

1. starting position이 `curve_ab` 초입이 맞는지
2. speed가 already too high였는지
3. heading source가 아직 `unknown` / `velocity_direction` 단계인지
4. ATS focus가 유지됐는지

### module throttle / brake가 안 먹음

현재 결론:

- 아직 미해결
- demo는 module longitudinal에 기대지 않는다

## 지금 하지 말 것

- complex intersection demo
- broad route following
- dense-local general active driving
- CV-first 확장
- wheel actuation

## 다음 세션 추천

1. gentle-curve demo 반복 재현성 고정
2. demo-only longitudinal shaping 추가 보정
3. 그 다음에만 curated denser corridor 1개 검토
4. route-following이나 general active는 아직 미루기
