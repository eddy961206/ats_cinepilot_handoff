# CV Observer + Handoff Harness Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a CV observer layer with lane/vehicle overlay and a durable in-repo handoff harness without replacing the existing constrained dense demo stack.

**Architecture:** Keep telemetry/graph/demo control as primary. Add a capture-backed CV observer module that produces overlay artifacts and optional guard signals, then thread those signals into the demo cage conservatively. Add docs/ops + machine-readable state early and keep them updated during the session.

**Tech Stack:** Python 3.11, OpenCV DNN, OpenCV image processing, existing ATS capture/telemetry/control stack, YAML/JSON docs state.

---

## Chunk 1: Baseline + Handoff Harness

### Task 1: Reproduce current dense baseline

**Files:**
- Modify: `docs/ops/EXPERIMENT_LOG.md`

- [ ] Run telemetry readiness.
- [ ] Run control readiness.
- [ ] Run current dense demo helper once.
- [ ] Record exact commands, commit, and outcomes in the experiment log.

### Task 2: Add durable ops docs/state scaffold

**Files:**
- Create: `docs/ops/CURRENT_STATE.md`
- Create: `docs/ops/ROADMAP.md`
- Create: `docs/ops/DECISIONS.md`
- Create: `docs/ops/EXPERIMENT_LOG.md`
- Create: `docs/ops/FAILED_ATTEMPTS.md`
- Create: `docs/ops/CHECKLISTS/demo_readiness.md`
- Create: `docs/ops/CHECKLISTS/experiment.md`
- Create: `docs/ops/CHECKLISTS/pr.md`
- Create: `docs/ops/CHECKLISTS/next_session_startup.md`
- Create: `docs/ops/NEXT_AGENT_BRIEF.md`
- Create: `state/latest_session_state.json`
- Create: `scripts/update_session_handoff.py`
- Modify: `.github/pull_request_template.md`
- Modify: `docs/RUNBOOK.md`

- [ ] Write the scaffold docs with current dense-demo truth.
- [ ] Add a small update helper that updates machine-readable state plus a managed facts section only.
- [ ] Add a narrow PR-template note that ops docs/state are part of session deliverables.
- [ ] Run the handoff update helper.

## Chunk 2: CV Observer Core

### Task 3: Add reusable CV domain/config types

**Files:**
- Create: `src/ats_cinepilot/perception/observer_types.py`
- Modify: `src/ats_cinepilot/ops/config.py`
- Test: `tests/test_cv_config.py`

- [ ] Add config-friendly dataclasses for lane observations, vehicle detections, lead vehicle, frame summary, and guard status.
- [ ] Add config defaults and validation hooks.
- [ ] Write tests for config loading.

### Task 4: Add pretrained vehicle detector wrapper

**Files:**
- Create: `src/ats_cinepilot/perception/vehicle_detector.py`
- Create: `scripts/download_cv_models.py`
- Test: `tests/test_vehicle_detector.py`

- [ ] Implement lazy model download and cache path handling.
- [ ] Pin exact model URL, version identifier, and checksum.
- [ ] Fail safely to lane-only mode when model asset is unavailable.
- [ ] Load TensorFlow SSD MobileNet v3 through OpenCV DNN.
- [ ] Filter detections to road vehicles and pick a lead candidate.
- [ ] Add tests for post-processing with synthetic outputs.

### Task 5: Add classical lane observer

**Files:**
- Create: `src/ats_cinepilot/perception/lane_observer.py`
- Test: `tests/test_lane_observer.py`

- [ ] Implement ROI crop + threshold + edge + Hough pipeline.
- [ ] Derive lane center, offset, and confidence.
- [ ] Add deterministic tests with synthetic lane images.
- [ ] Add at least one ATS saved-frame acceptance fixture check before enabling lane guard by default.

### Task 6: Add combined CV observer service

**Files:**
- Create: `src/ats_cinepilot/perception/cv_observer.py`
- Create: `src/ats_cinepilot/ops/artifacts.py`
- Test: `tests/test_cv_observer.py`

- [ ] Run lane + vehicle observers on capture frames.
- [ ] Save JSONL summaries.
- [ ] Save overlay frames/video when enabled.
- [ ] Keep show-window optional.

## Chunk 3: Overlay + Demo Integration

### Task 7: Expand overlay renderer

**Files:**
- Modify: `src/ats_cinepilot/ui/overlay.py`
- Test: `tests/test_overlay.py`

- [ ] Add lane polygon/lines rendering.
- [ ] Add vehicle boxes and lead vehicle label.
- [ ] Add graph/demo/CV status header.
- [ ] Add a smoke test for drawing.

### Task 8: Thread CV observer into app runtime

**Files:**
- Modify: `src/ats_cinepilot/app.py`
- Modify: `src/ats_cinepilot/ops/startup.py`
- Modify: `src/ats_cinepilot/domain/enums.py`
- Test: `tests/test_startup.py`
- Test: `tests/test_app_cv_guard.py`

- [ ] Start capture when CV is enabled even if HUD is disabled.
- [ ] Run observer each loop and expose status in recorder/logging.
- [ ] Add explicit CV guard reasons / state fields.
- [ ] Add tests that CV does not alter planner/path outputs when no guard is triggered.
- [ ] Keep active-control path conservative.

### Task 9: Add conservative CV guard logic

**Files:**
- Create: `src/ats_cinepilot/safety/cv_guard.py`
- Modify: `src/ats_cinepilot/safety/demo_cage.py`
- Test: `tests/test_cv_guard.py`

- [ ] Implement lane-confidence guard.
- [ ] Implement lead-vehicle risk as disengage-only in v1.
- [ ] Keep barrier/road-edge optional and explicit.
- [ ] Ensure no hidden steering control comes from CV.

## Chunk 4: Operator Commands + Verification

### Task 10: Add observer/demo configs and runner scripts

**Files:**
- Create: `configs/demo_active_dense_corridor_with_cv.yaml`
- Create: `configs/cv_observer_dense_corridor.yaml`
- Create: `scripts/run_cv_observer_dense_corridor.ps1`
- Create: `scripts/run_demo_active_dense_corridor_with_cv.ps1`
- Modify: `README.md`
- Modify: `docs/IMPLEMENTATION_STATUS.md`
- Modify: `docs/TASK_BOARD.md`
- Modify: `docs/RUNBOOK.md`

- [ ] Add explicit observer-only config.
- [ ] Add active-with-cv overlay/guard config.
- [ ] Add simple operator runners.
- [ ] Document commands, preconditions, artifact paths.

### Task 11: Verify end to end

**Files:**
- Modify: `docs/ops/CURRENT_STATE.md`
- Modify: `docs/ops/EXPERIMENT_LOG.md`
- Modify: `docs/ops/NEXT_AGENT_BRIEF.md`
- Modify: `state/latest_session_state.json`

- [ ] Run `pytest -q`.
- [ ] Run `ruff check .`.
- [ ] Run config validation.
- [ ] Run replay smoke.
- [ ] Run telemetry/control readiness.
- [ ] Run observer-only command and confirm overlay artifact output.
- [ ] Run dense demo with CV enabled and record whether guard behavior is partial or complete.
- [ ] Update ops docs/state with exact results.
