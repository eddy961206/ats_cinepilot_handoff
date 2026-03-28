# Live Active Demo Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first tightly constrained ATS live active demo on one low-speed corridor with a real control sink and a strict demo safety cage.

**Architecture:** Keep the existing telemetry, planner, control, and safety boundaries intact. Add a demo-only cage on top of the current safety policy, add config-driven external control-module loading, and keep the corridor fixed to the known toy-graph `ab` segment so live validation is narrow and reviewable.

**Tech Stack:** Python 3.11, pytest, Ruff, ATS shared memory v2, ETS2LA `scs-sdk-controller`, PowerShell helper scripts

---

## Chunk 1: Control path bring-up

### Task 1: Add config-driven external control module search paths

**Files:**
- Modify: `src/ats_cinepilot/bridge/scs_controls.py`
- Modify: `scripts/inspect_controls.py`
- Test: `tests/test_scs_controls.py`

- [ ] Step 1: Write a failing test for importing a control module from an explicit search path
- [ ] Step 2: Run the targeted test and confirm it fails for the right reason
- [ ] Step 3: Implement minimal search-path-aware control module loading
- [ ] Step 4: Run the targeted test and confirm it passes
- [ ] Step 5: Commit

### Task 2: Add explicit control micro-probe support

**Files:**
- Modify: `scripts/inspect_controls.py`
- Create: `tests/test_control_probe_cli.py` or extend probe coverage in `tests/test_live_diagnostics.py`

- [ ] Step 1: Write a failing test for explicit live-write arguments and dry-run behavior
- [ ] Step 2: Run the targeted test and confirm it fails
- [ ] Step 3: Implement steering/throttle/brake micro-pulse support with explicit opt-in
- [ ] Step 4: Run the targeted test and confirm it passes
- [ ] Step 5: Commit

## Chunk 2: Demo safety cage

### Task 3: Add a demo-only safety cage with corridor guards

**Files:**
- Create: `src/ats_cinepilot/safety/demo_cage.py`
- Modify: `src/ats_cinepilot/app.py`
- Modify: `src/ats_cinepilot/ops/startup.py`
- Modify: `src/ats_cinepilot/ops/config.py`
- Modify: `src/ats_cinepilot/domain/enums.py`
- Test: `tests/test_demo_cage.py`
- Test: `tests/test_startup.py`

- [ ] Step 1: Write failing demo-cage tests for arming, corridor bounds, graph contract, discontinuity, and manual override
- [ ] Step 2: Run the targeted tests and confirm they fail correctly
- [ ] Step 3: Implement the minimal demo cage and startup/config validation
- [ ] Step 4: Run the targeted tests and confirm they pass
- [ ] Step 5: Commit

### Task 4: Add control failure handling and demo status logging

**Files:**
- Modify: `src/ats_cinepilot/app.py`
- Modify: `tests/test_app_logging_snapshot.py`

- [ ] Step 1: Write a failing test for demo status snapshots or control-failure logging
- [ ] Step 2: Run the targeted test and confirm it fails
- [ ] Step 3: Implement minimal logging and write-failure neutralization
- [ ] Step 4: Run the targeted test and confirm it passes
- [ ] Step 5: Commit

## Chunk 3: Demo config and operator flow

### Task 5: Add the constrained demo config and helper scripts

**Files:**
- Create: `configs/demo_active_corridor.yaml`
- Create: `scripts/run_demo_active_corridor.ps1`
- Create: `scripts/demo_override_on.ps1`
- Create: `scripts/demo_override_off.ps1`
- Create: `scripts/install_scs_control_plugin.ps1`
- Test: `tests/test_config_loading.py`

- [ ] Step 1: Write a failing config-loading test for the demo profile
- [ ] Step 2: Run the targeted test and confirm it fails
- [ ] Step 3: Add the demo config and helper scripts with exact paths
- [ ] Step 4: Run the targeted test and confirm it passes
- [ ] Step 5: Commit

## Chunk 4: Verification and docs

### Task 6: Update docs and run full verification

**Files:**
- Modify: `docs/IMPLEMENTATION_STATUS.md`
- Modify: `docs/TASK_BOARD.md`
- Modify: `docs/LOCAL_SETUP.md`
- Modify: `docs/RUNBOOK.md`
- Modify: `README.md`

- [ ] Step 1: Update docs with the selected demo corridor, control path, and safety warnings
- [ ] Step 2: Run `pytest -q`
- [ ] Step 3: Run `ruff check .`
- [ ] Step 4: Run config validation, replay smoke, control probe, shadow qualification, and live active attempt if ATS is available
- [ ] Step 5: Commit
