# Dense Curated Active Demo Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first curated denser-corridor live active ATS demo using a dense local ATS source graph, explicit corridor contract, and the existing hybrid control path.

**Architecture:** Extract a short ordered edge sequence from the dense local ATS graph into a dedicated curated graph cache, load a corridor contract at runtime, and extend the demo safety cage and logging to enforce ordered corridor semantics before attempting a live active demo.

**Tech Stack:** Python, pytest, PowerShell, GitHub CLI, ATS shared-memory telemetry, hybrid control sink, YAML configs

---

## Chunk 1: Baseline + Contract Plumbing

### Task 1: Record the chosen corridor contract and add failing config/runtime tests

**Files:**
- Create: `configs/corridors/demo_dense_curated_corridor.yaml`
- Modify: `tests/test_config_loading.py`
- Modify: `tests/test_demo_cage.py`

- [ ] **Step 1: Write failing tests for dense corridor config visibility and ordered edge sequence expectations**
- [ ] **Step 2: Run targeted tests to verify they fail**
- [ ] **Step 3: Add the corridor contract artifact**
- [ ] **Step 4: Add minimal runtime/config plumbing to load the new contract fields**
- [ ] **Step 5: Re-run targeted tests until green**
- [ ] **Step 6: Commit**

### Task 2: Add a curated graph extraction utility with tests

**Files:**
- Create: `scripts/build_curated_corridor_graph.py`
- Modify: `src/ats_cinepilot/map/cache.py`
- Create: `tests/test_curated_corridor_graph.py`

- [ ] **Step 1: Write failing tests for extracting a smaller ordered graph from a source cache**
- [ ] **Step 2: Run targeted tests to verify they fail**
- [ ] **Step 3: Implement the smallest graph extraction helper and script**
- [ ] **Step 4: Generate `data/maps/cache/demo_dense_curated_corridor_graph.json` from the chosen contract**
- [ ] **Step 5: Re-run targeted tests until green**
- [ ] **Step 6: Commit**

## Chunk 2: Safety Cage + Runner

### Task 3: Extend demo cage to enforce ordered corridor semantics

**Files:**
- Modify: `src/ats_cinepilot/safety/demo_cage.py`
- Modify: `src/ats_cinepilot/app.py`
- Modify: `tests/test_demo_cage.py`

- [ ] **Step 1: Write failing tests for edge-sequence progression, edge-index logging, and out-of-sequence disengage**
- [ ] **Step 2: Run targeted tests to verify they fail**
- [ ] **Step 3: Implement minimal ordered corridor tracking and diagnostics**
- [ ] **Step 4: Re-run targeted tests until green**
- [ ] **Step 5: Commit**

### Task 4: Add dense curated demo config and runner

**Files:**
- Create: `configs/demo_active_dense_corridor.yaml`
- Create: `scripts/run_demo_active_dense_corridor.ps1`
- Modify: `src/ats_cinepilot/ops/startup.py`
- Modify: `tests/test_startup.py`

- [ ] **Step 1: Write failing tests for startup summary / startup validation with the new dense demo config**
- [ ] **Step 2: Run targeted tests to verify they fail**
- [ ] **Step 3: Implement the config, runner, and startup summary updates**
- [ ] **Step 4: Re-run targeted tests until green**
- [ ] **Step 5: Commit**

## Chunk 3: Verification + Docs

### Task 5: Reproduce the gentle-curve baseline and validate dense corridor shadow/active behavior

**Files:**
- Modify: `docs/ACTIVE_DEMO_EXPERIMENT_LOG.md`
- Modify: `docs/IMPLEMENTATION_STATUS.md`
- Modify: `docs/TASK_BOARD.md`
- Modify: `docs/RUNBOOK.md`
- Modify: `README.md`

- [ ] **Step 1: Run readiness, baseline, and dense corridor qualification commands**
- [ ] **Step 2: Run the first live dense curated active demo attempt if ATS is available**
- [ ] **Step 3: Record exact commands, outputs, and results in docs**
- [ ] **Step 4: Commit**

### Task 6: Full verification, review, PR, merge

**Files:**
- Modify: PR body only

- [ ] **Step 1: Run full verification**
- [ ] **Step 2: Request code review and address findings**
- [ ] **Step 3: Push branch and open PR with gh**
- [ ] **Step 4: Merge with gh into the correct target branch if all checks and live verification are complete**
- [ ] **Step 5: Delete the source branch if possible**
