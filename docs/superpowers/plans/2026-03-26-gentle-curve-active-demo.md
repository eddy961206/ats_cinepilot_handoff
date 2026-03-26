# Gentle Curve Active Demo Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 기존 직선 active demo를 유지하면서, 시작 직후부터 완만하게 휘는 전용 corridor에서 live closed-loop steering이 보이는 constrained active demo를 추가한다.

**Architecture:** dense graph나 route source로 넓히지 않고, dedicated toy gentle-curve graph + dedicated config/runner + demo summary 확장으로 해결한다. control path는 기존 `hybrid`를 그대로 쓰고, safety cage는 corridor contract와 curve thresholds를 더 명시적으로 고정한다.

**Tech Stack:** Python, PowerShell, ATS shared memory telemetry, hybrid control sink, JSON graph cache, pytest, ruff

---

## Chunk 1: Baseline And Curved Corridor Assets

### Task 1: straight baseline 재현 흔적 고정

**Files:**
- Modify: `docs/IMPLEMENTATION_STATUS.md`
- Modify: `docs/TASK_BOARD.md`

- [ ] **Step 1: 현재 straight demo baseline 검증 명령을 다시 실행**

Run:

```powershell
.\.venv\Scripts\python -m pytest -q
.\.venv\Scripts\python -m ruff check .
.\.venv\Scripts\ats-cinepilot.exe check-config --config configs/demo_active_corridor.yaml
.\.venv\Scripts\python.exe scripts/inspect_telemetry.py --config configs/demo_active_corridor.yaml --frames 3 --require-ready
.\.venv\Scripts\python.exe scripts/inspect_controls.py --config configs/demo_active_corridor.yaml --dry-run --require-ready
```

- [ ] **Step 2: straight helper를 한 번 더 실행해 baseline log를 남긴다**

Run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_demo_active_corridor.ps1 -ShadowSteps 20 -ActiveSteps 80 -ActiveCountdownSeconds 8
```

- [ ] **Step 3: 결과를 status/task docs 메모로 남긴다**

- [ ] **Step 4: commit**

```bash
git add docs/IMPLEMENTATION_STATUS.md docs/TASK_BOARD.md
git commit -m "docs: [baseline] straight active demo 재현 기록 추가"
```

### Task 2: gentle curve graph/cache와 config 골격 추가

**Files:**
- Create: `data/maps/cache/demo_gentle_curve_graph.json`
- Create: `configs/demo_active_gentle_curve.yaml`
- Create: `scripts/run_demo_active_gentle_curve.ps1`
- Test: `tests/test_config_loading.py`
- Test: `tests/test_startup.py`

- [ ] **Step 1: gentle curve config를 검증하는 failing test 추가**

테스트 포인트:
- new config loads
- graph source / alignment / approved edge / hybrid sink contract가 expected 값인지

- [ ] **Step 2: 새 config를 아직 만들기 전 테스트를 실행해 실패를 확인**

Run:

```powershell
.\.venv\Scripts\python -m pytest -q tests/test_config_loading.py tests/test_startup.py
```

- [ ] **Step 3: dedicated curve graph cache, config, runner를 최소 구현**

구현 포인트:
- 곡선은 시작부 short straight + gentle left curve
- `hybrid` sink 유지
- `map.source_name=toy_gentle_curve_graph`
- dedicated log path 사용

- [ ] **Step 4: 같은 테스트를 다시 돌려 통과 확인**

- [ ] **Step 5: commit**

```bash
git add data/maps/cache/demo_gentle_curve_graph.json configs/demo_active_gentle_curve.yaml scripts/run_demo_active_gentle_curve.ps1 tests/test_config_loading.py tests/test_startup.py
git commit -m "feat: [demo] gentle curve corridor 자산 추가"
```

## Chunk 2: Safety Cage And Demo Summary

### Task 3: curved demo safety / startup wording 강화

**Files:**
- Modify: `src/ats_cinepilot/ops/startup.py`
- Modify: `src/ats_cinepilot/safety/demo_cage.py`
- Test: `tests/test_demo_cage.py`
- Test: `tests/test_startup.py`

- [ ] **Step 1: curve demo 전용 contract를 명시하는 failing tests 추가**

테스트 포인트:
- foreground focus warning이 startup summary에 드러남
- curve demo config가 strict graph/alignment/edge contract를 유지
- preview path / direction / thresholds failure가 여전히 즉시 block

- [ ] **Step 2: targeted tests를 실행해 실패 확인**

Run:

```powershell
.\.venv\Scripts\python -m pytest -q tests/test_demo_cage.py tests/test_startup.py
```

- [ ] **Step 3: minimal production change 구현**

구현 포인트:
- startup summary에 curve demo contract와 focus requirement 명시
- 필요하면 demo cage config parsing 보강

- [ ] **Step 4: targeted tests green 확인**

- [ ] **Step 5: commit**

```bash
git add src/ats_cinepilot/ops/startup.py src/ats_cinepilot/safety/demo_cage.py tests/test_demo_cage.py tests/test_startup.py
git commit -m "feat: [demo] gentle curve safety preflight 강화"
```

### Task 4: demo log summary에 steering metrics 추가

**Files:**
- Modify: `scripts/summarize_shadow_log.py`
- Test: `tests/test_shadow_log_summary.py`

- [ ] **Step 1: steering/throttle/brake/demo guard summary failing test 추가**

테스트 포인트:
- steering_abs_max
- non_trivial_steering_count
- throttle_command_count
- brake_command_count
- demo_guard_reason_counts

- [ ] **Step 2: targeted test를 실행해 실패 확인**

Run:

```powershell
.\.venv\Scripts\python -m pytest -q tests/test_shadow_log_summary.py
```

- [ ] **Step 3: summary script를 최소 확장**

- [ ] **Step 4: targeted test green 확인**

- [ ] **Step 5: commit**

```bash
git add scripts/summarize_shadow_log.py tests/test_shadow_log_summary.py
git commit -m "feat: [demo] active steering 요약 지표 추가"
```

## Chunk 3: Live Curved Demo Validation

### Task 5: curved shadow qualification과 active attempt

**Files:**
- Modify: `README.md`
- Modify: `docs/IMPLEMENTATION_STATUS.md`
- Modify: `docs/TASK_BOARD.md`
- Modify: `docs/RUNBOOK.md`

- [ ] **Step 1: full regression 실행**

Run:

```powershell
.\.venv\Scripts\python -m pytest -q
.\.venv\Scripts\python -m ruff check .
.\.venv\Scripts\ats-cinepilot.exe check-config --config configs/demo_active_gentle_curve.yaml
.\.venv\Scripts\ats-cinepilot.exe run --config configs/profiles/replay_demo.yaml --mode shadow --steps 5
.\.venv\Scripts\python.exe scripts/inspect_telemetry.py --config configs/demo_active_gentle_curve.yaml --frames 3 --require-ready
.\.venv\Scripts\python.exe scripts/inspect_controls.py --config configs/demo_active_gentle_curve.yaml --dry-run --require-ready
```

- [ ] **Step 2: curved shadow qualification 실행**

Run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_demo_active_gentle_curve.ps1 -ShadowSteps 25 -ActiveSteps 0 -ActiveCountdownSeconds 0 -ShadowOnly
```

- [ ] **Step 3: curved active demo 실행**

Run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_demo_active_gentle_curve.ps1 -ShadowSteps 25 -ActiveSteps 120 -ActiveCountdownSeconds 8
```

- [ ] **Step 4: summary 출력과 로그를 확인해 steering이 의미 있게 non-zero인지 검토**

Run:

```powershell
.\.venv\Scripts\python scripts\summarize_shadow_log.py --input data\logs\demo_active_gentle_curve.jsonl
```

- [ ] **Step 5: docs를 reality-based로 업데이트**

- [ ] **Step 6: commit**

```bash
git add README.md docs/IMPLEMENTATION_STATUS.md docs/TASK_BOARD.md docs/RUNBOOK.md
git commit -m "docs: [demo] gentle curve active 결과 반영"
```

