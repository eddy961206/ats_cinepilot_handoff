# Runbook

## 현재 목표

지금 운영 목표는 **dense curated active demo + CV observer overlay를 보수적으로 운영**하는 거야.

즉:

- telemetry는 live
- control은 live
- corridor는 하나
- graph는 dense-local source에서 뽑은 curated chain
- run 시작 때 corridor를 현재 truck 위치에 맞춰 runtime fit
- speed는 낮게
- safety cage는 빡세게
- CV는 observer / overlay / disengage-only guard다

general autopilot 운영 문서가 아니다.

## base 상태 확인

작업 시작 전에 먼저 확인해.

- `main`이 `6eb557371a4806595f4e4fbfa0c28356367bcfd4` 이후 상태인지
- stale branch에서 새 feature를 시작하지 않는지

## 세션 시작 순서

새 agent나 긴 세션 복귀 시엔 먼저 이 둘부터 봐.

- `docs/ops/NEXT_AGENT_BRIEF.md`
- `docs/ops/CURRENT_STATE.md`

그 다음 필요하면:

- `docs/ops/EXPERIMENT_LOG.md`
- `state/latest_session_state.json`

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

### dense curated corridor CV observer

- config: `configs/cv_observer_dense_corridor.yaml`
- helper: `scripts/run_cv_observer_dense_corridor.ps1`
- artifact dir: `data/artifacts/cv/observer_dense_corridor`
- summary log: `data/logs/cv_observer_dense_corridor.cv.jsonl`

### dense curated corridor active + CV

- config: `configs/demo_active_dense_corridor_with_cv.yaml`
- helper: `scripts/run_demo_active_dense_corridor_with_cv.ps1`
- artifact dir: `data/artifacts/cv/demo_active_dense_corridor`
- summary log: `data/logs/demo_active_dense_corridor_with_cv.cv.jsonl`

## hybrid sink 의미

- steering / blinkers -> module sink
- throttle / brake -> keyboard sink

dense demo와 dense+CV demo도 이 hybrid path를 그대로 쓴다.

## preflight

### 1. 환경

```powershell
.\scripts\setup_venv.ps1
```

### 2. config check

```powershell
.\.venv\Scripts\ats-cinepilot check-config --config configs\demo_active_dense_corridor.yaml
.\.venv\Scripts\ats-cinepilot check-config --config configs\cv_observer_dense_corridor.yaml
.\.venv\Scripts\ats-cinepilot check-config --config configs\demo_active_dense_corridor_with_cv.yaml
```

### 3. telemetry probe

```powershell
.\.venv\Scripts\python scripts\inspect_telemetry.py --config configs\demo_active_dense_corridor.yaml --frames 3 --require-ready
.\.venv\Scripts\python scripts\inspect_telemetry.py --config configs\demo_active_dense_corridor_with_cv.yaml --frames 3 --require-ready
```

### 4. control probe

```powershell
.\.venv\Scripts\python scripts\inspect_controls.py --config configs\demo_active_dense_corridor.yaml --dry-run --require-ready
.\.venv\Scripts\python scripts\inspect_controls.py --config configs\demo_active_dense_corridor_with_cv.yaml --dry-run --require-ready
```

성공 기준:

- `telemetry status: telemetry ready`
- `hybrid status: control path ready`

### 5. CV model 준비

```powershell
.\.venv\Scripts\python scripts\download_cv_models.py --config configs\cv_observer_dense_corridor.yaml
```

## operator preconditions

반드시 맞춰.

- ATS running
- ATS window maximized or full-screen 권장
- drivable state
- engine on
- forward gear
- parking brake 해제
- verified freeway corridor chain 위
- dense active demo에서는 ATS 창 foreground 유지
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

## observer-only CV run

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_cv_observer_dense_corridor.ps1 -Steps 80
```

이 run은:

- overlay window를 띄울 수 있다
- active control은 하지 않는다
- annotated frame / mp4 / jsonl을 남긴다

## dense curated active demo with CV

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_demo_active_dense_corridor_with_cv.ps1 -ShadowSteps 8 -ActiveSteps 80 -ActiveCountdownSeconds 3
```

이 run은:

- dense runtime fit을 수행한다
- 기존 hybrid active demo를 그대로 쓴다
- CV overlay artifact를 함께 남긴다
- lead vehicle guard는 `disengage_only`다

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

## 현재 실제 CV result

observer-only verified result:

- `frames=80`
- `lane_detected=80`
- `lane_conf=[1.000, 1.000]`
- `lead_detected=0`

dense active + CV verified result:

- `steps=88`
- `safety={MATCH_LOST: 17, ROUTE_CONFIDENCE_LOW: 2, DEMO_GUARD: 21, NONE: 48}`
- `match=[0.700, 1.000]`
- `route=[0.480, 0.700]`
- `cte_max=0.039`
- `steering_abs_max=0.300`
- `non_trivial_steering_count=20`
- `lane_detected=88`
- `lead_detected=0`

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

### observer-only run은 overlay는 되는데 graph safety가 안 좋음

- observer-only config는 runtime fit 없이 checked-in graph를 바로 본다
- overlay 품질 검증용으로만 써
- dense demo fitness 평가는 반드시 runtime-fit helper run으로 판단해

## 지금 하지 말 것

- general route-following
- complex intersection demo
- dense-local general active driving
- CV-first 확장
- wheel actuation
- CV-only control

## 다음 세션 추천

1. traffic가 있는 장면에서 vehicle detector / lead guard evidence 추가
2. dense curated corridor demo 반복 재현성 고정
3. curated multi-edge corridor 1개로 확장
4. route-aware demo는 아직 미루기
