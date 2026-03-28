# Runbook

## 현재 목표

지금 운영 목표는 **first curated denser-corridor constrained live active demo 반복 재현**이야.

즉:

- telemetry는 live
- control은 live
- corridor는 하나
- graph는 dense-local source에서 뽑은 curated chain
- run 시작 때 corridor를 현재 truck 위치에 맞춰 runtime fit
- speed는 낮게
- safety cage는 빡세게

general autopilot 운영 문서가 아니다.

## base 상태 확인

작업 시작 전에 먼저 확인해.

- `main`이 consolidation PR `#10` 이후 상태인지
- `main@880cfa5e17da5a9aca8ad304ed350b35dee72021` 이후에서 작업하는지
- stale branch에서 새 feature를 시작하지 않는지

## 현재 선택 demo path

### straight baseline

- config: `configs/demo_active_corridor.yaml`
- helper: `scripts/run_demo_active_corridor.ps1`

### gentle curve demo

- config: `configs/demo_active_gentle_curve.yaml`
- helper: `scripts/run_demo_active_gentle_curve.ps1`

### dense curated corridor demo

- base config: `configs/demo_active_dense_corridor.yaml`
- base contract: `configs/corridors/demo_dense_curated_corridor.yaml`
- helper: `scripts/run_demo_active_dense_corridor.ps1`
- runtime overlay: `data/runtime/demo_dense_curated_corridor.runtime.yaml`
- runtime graph: `data/maps/cache/demo_dense_curated_corridor.runtime.json`

## hybrid sink 의미

- steering / blinkers -> module sink
- throttle / brake -> keyboard sink

dense demo도 이 hybrid path를 그대로 쓴다.

## preflight

### 1. 환경

```powershell
.\scripts\setup_venv.ps1
```

### 2. config check

```powershell
.\.venv\Scripts\ats-cinepilot check-config --config configs\demo_active_dense_corridor.yaml
```

### 3. telemetry probe

```powershell
.\.venv\Scripts\python scripts\inspect_telemetry.py --config configs\demo_active_dense_corridor.yaml --frames 3 --require-ready
```

### 4. control probe

```powershell
.\.venv\Scripts\python scripts\inspect_controls.py --config configs\demo_active_dense_corridor.yaml --dry-run --require-ready
```

성공 기준:

- `telemetry status: telemetry ready`
- `hybrid status: control path ready`

## operator preconditions

반드시 맞춰.

- ATS running
- drivable state
- engine on
- forward gear
- parking brake 해제
- verified freeway corridor chain 위
- ATS 창 foreground 유지
- operator 손은 즉시 takeover 가능

## 현재 dense corridor 의미

이 demo는 “아무 dense road나” 가는 게 아니야.

- checked-in source chain은 고정이다
- helper가 run 시작 전에 현재 truck 위치를 그 chain에 fit해서 runtime translation을 만든다
- 즉 같은 freeway chain 위에만 놓여 있으면 exact start 좌표를 수동으로 맞출 필요는 없다

## dense curated active demo

실행:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_demo_active_dense_corridor.ps1 -ShadowSteps 12 -ActiveSteps 140 -ActiveCountdownSeconds 3
```

helper가 하는 일:

1. override clear
2. telemetry probe
3. stop preflight
4. runtime corridor fit
5. runtime graph export
6. config check
7. control probe
8. shadow qualification
9. stop preflight
10. countdown
11. active run
12. log summary 출력

## 현재 실제 dense result

verified run:

```text
steps=152
safety={MATCH_LOST: 31, ROUTE_CONFIDENCE_LOW: 4, DEMO_GUARD: 25, NONE: 92}
first_MATCH_LOST=1
first_ROUTE_CONFIDENCE_LOW=32
match=[0.717, 1.000]
route=[0.487, 0.700]
cte_max=0.030
near=[0.000, 0.030]
cand=[1, 1]
steering_abs_max=0.300
non_trivial_steering_count=35
throttle_command_count=31
brake_command_count=121
demo_guard_reasons={bootstrap: 31, arming: 16, speed_cap_exceeded: 13, armed: 92}
```

해석:

- dense curated corridor에서도 steering이 실제로 걸렸다
- throttle / brake도 같은 run 안에서 실제로 적용됐다
- review fix 이후에도 runtime fit이 `dense_seg_04` 단일 edge corridor로 trim된 상태에서 candidate count는 계속 `1`
- `safety=NONE`이 `92` step 유지돼 demo milestone로는 충분하다

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
- keyboard sink focus / platform issue

### dense helper가 바로 끊김

먼저 이 넷부터 봐.

1. truck가 checked-in dense corridor source chain 위였는지
2. ATS 창이 foreground였는지
3. vehicle stop preflight가 실제로 끝났는지
4. override flag가 켜져 있지 않은지

### dense demo에서 brake assist가 많음

현재 결론:

- 아직 demo-only longitudinal shaping이 거칠다
- module longitudinal에 기대지 않는다

## 지금 하지 말 것

- general route-following
- complex intersection demo
- dense-local general active driving
- CV-first 확장
- wheel actuation

## 다음 세션 추천

1. dense curated corridor demo 반복 재현성 고정
2. demo-only longitudinal shaping 추가 보정
3. curated multi-edge corridor 1개로 확장
4. route-aware demo는 아직 미루기
