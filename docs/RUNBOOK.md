# Runbook

## 현재 목표

지금 이 repo의 운영 목표는 **첫 constrained live active demo 반복 재현**이야.

즉:

- telemetry는 live
- control은 live
- corridor는 하나
- speed는 낮게
- safety cage는 빡세게

general autopilot 운영 문서가 아니다.

## base 상태 확인

작업 시작 전에 꼭 먼저 확인해.

- `main`이 PR #6/#7까지 포함하는지
- 아니라면 stale `main`에서 새 기능 시작하지 않는지
- stacked lineage가 필요한지

## 현재 선택 demo path

- config: `configs/demo_active_corridor.yaml`
- telemetry: `shared_memory_v2`
- graph: `toy_graph`
- alignment: `anchored_local_toy_graph`
- approved edge: `ab`
- sink: `hybrid`

`hybrid` 의미:

- steering / blinkers -> module sink
- throttle / brake -> keyboard sink

## preflight

### 1. 환경

```powershell
.\scripts\setup_venv.ps1
```

### 2. config check

```powershell
.\.venv\Scripts\ats-cinepilot check-config --config configs\demo_active_corridor.yaml
```

### 3. telemetry probe

```powershell
.\.venv\Scripts\python scripts\inspect_telemetry.py --config configs\demo_active_corridor.yaml --frames 3 --require-ready
```

성공 기준:

- `telemetry status: telemetry ready`
- `SCSTelemetrySharedv2_ats` visible
- decode OK

### 4. control probe

```powershell
.\.venv\Scripts\python scripts\inspect_controls.py --config configs\demo_active_corridor.yaml --dry-run --require-ready
```

성공 기준:

- module path ready
- keyboard path ready
- hybrid status ready

## live micro validation

### steering path

module steering pulse는 visual confirmation으로 확인한다.

예:

```powershell
.\.venv\Scripts\python scripts\inspect_controls.py --config configs\demo_active_corridor.yaml --live-write --pulse-axis steering --value 1.0 --hold-ms 3000
```

확인 포인트:

- 핸들이나 앞바퀴가 실제로 움직이는지

### longitudinal path

keyboard longitudinal은 telemetry로 확인 가능하다.

이번 세션의 실제 증거:

- hybrid micro-probe에서 speed `3.611 -> 13.777`
- brake에서 `15.340 -> 0.000`

## constrained active demo

실행:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_demo_active_corridor.ps1 -ShadowSteps 20 -ActiveSteps 80 -ActiveCountdownSeconds 8
```

helper가 하는 일:

1. override clear
2. config check
3. telemetry probe
4. control probe
5. shadow qualification
6. countdown
7. active run

## operator preconditions

반드시 맞춰.

- ATS running
- drivable state
- forward gear
- parking brake 해제
- approved corridor 근처
- ATS 창 foreground 유지
- operator 손은 즉시 takeover 가능

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

## 이번 세션의 실제 active 결과

short active demo attempt:

```text
bootstrap: 0.00 -> 2.54 m/s
armed: 2.51 -> 4.10 m/s
speed_cap_exceeded 후 brake assist: 5.34 -> 1.95 m/s
```

해석:

- throttle 적용됨
- brake assist 적용됨
- steering path는 같은 세션에서 module pulse로 별도 visual 확인됨
- active corridor 자체는 직선 toy segment라 active run 중 steering magnitude는 작았다

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

참고:

- hidden child process에서 keyboard input은 흔들릴 수 있었다
- 같은 프로세스 direct run이나 human-run PowerShell helper는 더 안정적이었다

### module throttle / brake가 안 먹음

현재 결론:

- 아직 미해결
- `aforward`, `activate`, `drive`, `parkingbrake=false` 조합을 telemetry와 같이 찍어도 속도 상승이 없었다
- 그래서 demo는 module longitudinal에 기대지 않는다

## 지금 하지 말 것

- complex intersection demo
- broad route following
- Active Mode 일반화
- CV-first 확장
- wheel actuation

## 다음 세션 추천

1. human-run 재현성 강화
2. focus preflight 보강
3. module longitudinal isolate
4. 그 다음에만 corridor를 조금 넓히기
