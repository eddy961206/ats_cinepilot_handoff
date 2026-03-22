# Runbook

## 반복 사이클

1. `.\scripts\setup_venv.ps1`
2. `ats-cinepilot check-config --config ...`
3. `python scripts\inspect_telemetry.py --config ...`
4. replay shadow smoke
5. live shadow smoke
6. 로그 확인
7. 필요한 경우 HUD calibration
8. 그다음에만 control probe

## 우선순위

### 1단계
- live telemetry stability
- absolute pose 계약 찾기
- matcher confidence 확인

### 2단계
- HUD route hint 연결
- longer shadow run
- shadow replay 검토

### 3단계
- control plugin path
- Active Mode 전용 safety hardening

## 로컬 codex 작업 원칙

- 한 번에 한 층만 건드려
- 변경 후 바로 smoke test
- replay와 live를 둘 다 다시 확인해
- confidence가 낮으면 해제부터 강화해
- 딥러닝 모델은 나중

## PR Workflow

- 항상 `main`에서 `codex/` 브랜치를 새로 만들어
- 항상 PR을 열고 리뷰 가능한 diff 상태로 남겨
- 리뷰 없이 self-merge 하지 마
- PR 본문에는 정확한 명령어와 실제 결과를 그대로 적어

## 실제 해석 규칙

### `inspect_telemetry.py`
- `telemetry status: telemetry ready`
  - mapping visible + decode 성공 + sampled frame update token 변화 확인
- `mapping visible but unsupported layout`
  - mapping은 열렸지만 이 reader가 아는 layout이 아님
- `mapping visible but stale/non-updating`
  - mapping은 열렸지만 sampled frame이 안 바뀜
- 현재 기본 live config는 `configs/live_probe_moza_shared_memory.yaml`
- 현재 기본 mapping 이름은 `SCSTelemetrySharedv2_ats`

### `ats-cinepilot run ... --mode shadow`
- startup summary에서 최소 아래를 본다:
  - `telemetry_source`
  - `mapping`
  - `control_sink`
  - `route_provider`
  - `hud_capture`
- live shadow 성공 기준:
  - 앱이 예외 없이 step loop를 돈다
  - `fresh_ms`가 stale로 치솟지 않는다
  - recorder가 생성된다

### `inspect_controls.py`
- 아직 telemetry 다음 단계다
- `module import: FAILED`면 Python 쪽 `scscontroller.py`가 아직 없다
- dry-run은 안전하지만, 이것만으로 ATS가 실제로 명령을 수신한다고 증명되지는 않는다
