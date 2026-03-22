# Runbook

## 반복 사이클

1. `.\scripts\setup_venv.ps1`
2. `ats-cinepilot check-config --config ...`
3. `python scripts\inspect_telemetry.py --config ...`
4. `python scripts\inspect_controls.py --config ... --dry-run`
5. HUD screenshot 확보
6. `python scripts\calibrate_hud.py --config ... --image ...`
7. replay shadow 먼저
8. 실 telemetry shadow
9. 로그/replay 확인
10. 임계값 / gain 수정
11. 다시 반복

## 우선순위

### 1단계
- telemetry
- control
- map cache
- matcher

### 2단계
- HUD route mask
- turn bias
- shadow mode overlay

### 3단계
- active mode
- branch handling
- speed profile tuning

## 로컬 codex 작업 원칙

- 한 번에 한 층만 건드려
- 변경 후 바로 smoke test
- replay를 남겨
- confidence가 낮으면 해제부터 강화해
- 딥러닝 모델은 나중

## 실제 해석 규칙

### `inspect_telemetry.py`
- `Local\SCSTelemetry: not visible`이면 shared-memory telemetry plugin이 아직 안 보이는 상태다.
- `http probe: FAILED`이면 JSON wrapper endpoint가 아직 안 떠 있거나 포트/스키마가 다르다.

### `inspect_controls.py`
- `module import: FAILED`면 Python 쪽 `scscontroller.py`가 아직 없다.
- `named mapping probe before attach: ... not visible`면 ATS/plugin이 아직 control memory를 열지 않았을 가능성이 크다.
- dry-run은 안전하지만, 이것만으로 ATS가 실제로 명령을 수신한다고 증명되지는 않는다.

### replay shadow
- 지금은 `configs/profiles/replay_demo.yaml` 하나만으로 바로 돌릴 수 있다.
- step 로그에서 최소한 아래를 본다:
  - `fresh_ms`
  - `match`
  - `route`
  - `branch`
  - `target`
  - `safety`
