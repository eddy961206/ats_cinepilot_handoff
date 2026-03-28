# Curated Dense Corridor Active Demo Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first curated dense-corridor live active ATS demo on updated `main`, using the existing hybrid control path and a strict demo cage.

**Architecture:** Keep the existing active-demo stack intact, but replace the toy graph with a generated dense local subgraph built from one explicit ATS edge chain. Extend the demo cage just enough to enforce ordered corridor semantics and start constraints without widening into general route-following.

**Tech Stack:** Python, pytest, PowerShell runner scripts, YAML configs, GitHub CLI.

---

## Chunk 1: Base Reproduction and Corridor Asset Generation

### Task 1: Reproduce the current gentle-curve baseline

**Files:**
- Modify: `docs/ACTIVE_DEMO_EXPERIMENT_LOG.md`
- Test: runtime commands only

- [ ] **Step 1: Run gentle-curve readiness commands**

Run:

```powershell
.\.venv\Scripts\python.exe scripts\inspect_telemetry.py --config configs\demo_active_gentle_curve.yaml --frames 3 --require-ready
.\.venv\Scripts\python.exe scripts\inspect_controls.py --config configs\demo_active_gentle_curve.yaml --dry-run --require-ready
```

- [ ] **Step 2: Re-run the gentle-curve baseline helper**

Run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_demo_active_gentle_curve.ps1 -ShadowSteps 25 -ActiveSteps 120 -ActiveCountdownSeconds 10
```

- [ ] **Step 3: Record the fresh baseline result**

Capture the log summary in `docs/ACTIVE_DEMO_EXPERIMENT_LOG.md` and docs updated later.

### Task 2: Add a reproducible curated dense corridor extractor

**Files:**
- Create: `scripts/extract_curated_corridor_graph.py`
- Create: `tests/test_extract_curated_corridor_graph.py`
- Modify: `docs/ACTIVE_DEMO_EXPERIMENT_LOG.md`

- [ ] **Step 1: Write the failing extraction tests**
- [ ] **Step 2: Run the extraction tests and confirm failure**
- [ ] **Step 3: Implement minimal extraction logic**
- [ ] **Step 4: Generate `data/maps/cache/demo_dense_curated_corridor_graph.json` from the selected edge chain**
- [ ] **Step 5: Re-run the extraction tests and confirm pass**

## Chunk 2: Dense Corridor Contract and Demo Cage

### Task 3: Add the human-readable dense corridor contract/configs

**Files:**
- Create: `configs/corridors/demo_dense_curated_corridor.yaml`
- Create: `configs/demo_active_dense_corridor.yaml`
- Create: `scripts/run_demo_active_dense_corridor.ps1`
- Test: `tests/test_config_loading.py`

- [ ] **Step 1: Write failing config-loading expectations for the new dense demo config**
- [ ] **Step 2: Run targeted config tests and confirm failure**
- [ ] **Step 3: Add the corridor config and runner script**
- [ ] **Step 4: Re-run config tests and confirm pass**

### Task 4: Extend the demo cage for ordered dense corridor semantics

**Files:**
- Modify: `src/ats_cinepilot/safety/demo_cage.py`
- Modify: `src/ats_cinepilot/app.py`
- Modify: `tests/test_demo_cage.py`
- Modify: `tests/test_app_logging_snapshot.py`

- [ ] **Step 1: Write failing tests for ordered edge sequence and start-window enforcement**
- [ ] **Step 2: Run targeted demo-cage tests and confirm failure**
- [ ] **Step 3: Implement minimal ordered-corridor logic and logging fields**
- [ ] **Step 4: Re-run targeted tests and confirm pass**

## Chunk 3: Verification and Docs

### Task 5: Shadow qualification and live dense active demo

**Files:**
- Modify: `docs/ACTIVE_DEMO_EXPERIMENT_LOG.md`
- Modify: `docs/IMPLEMENTATION_STATUS.md`
- Modify: `docs/TASK_BOARD.md`
- Modify: `docs/RUNBOOK.md`
- Modify: `README.md`

- [ ] **Step 1: Run dense demo config validation**
- [ ] **Step 2: Run dense shadow qualification**
- [ ] **Step 3: If ATS is available, run one real dense active demo attempt**
- [ ] **Step 4: Capture steering/safety/corridor adherence metrics in docs**

### Task 6: Full verification, PR, review, merge

**Files:**
- Modify: docs above as needed

- [ ] **Step 1: Run full verification**

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\ats-cinepilot.exe check-config --config configs\demo_active_dense_corridor.yaml
.\.venv\Scripts\ats-cinepilot.exe run --config configs\profiles\replay_demo.yaml --mode shadow --steps 5
```

- [ ] **Step 2: Request code review before PR merge**
- [ ] **Step 3: Create PR with `gh pr create`**
- [ ] **Step 4: If verification is complete, merge with `gh pr merge --merge --delete-branch`**
