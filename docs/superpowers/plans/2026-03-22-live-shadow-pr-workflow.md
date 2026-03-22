# Live Shadow PR Workflow Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Standardize PR-first development and leave the repo with one concrete, reproducible ATS-backed Shadow Mode validation path.

**Architecture:** Keep the existing bridge and safety boundaries intact. Select one live telemetry path as the default operator path, improve probe/startup diagnostics around that path, then document and verify the exact operator workflow without weakening disengagement behavior.

**Tech Stack:** Python 3.11, pytest, ruff, PowerShell, git, GitHub PR workflow

---

### Task 1: PR Workflow Scaffold

**Files:**
- Create: `.github/pull_request_template.md`
- Modify: `docs/CODEX_HANDOFF.md` or `docs/RUNBOOK.md`

- [ ] **Step 1: Add failing test or validation target**
No code test needed. Validation target is a rendered PR template file plus documented PR workflow section in docs.

- [ ] **Step 2: Add the PR template with required review fields**

- [ ] **Step 3: Add a concise PR workflow section to docs**

- [ ] **Step 4: Verify files render clearly**
Run: `Get-Content -Raw .github/pull_request_template.md`
Expected: all required reviewer fields present.

- [ ] **Step 5: Commit**
Run: `git commit -m "docs: [workflow] PR 템플릿과 리뷰 절차 추가"`

### Task 2: Live Telemetry Path Selection And Diagnostics

**Files:**
- Modify: `configs/*.yaml`
- Modify: `src/ats_cinepilot/bootstrap.py`
- Modify: `src/ats_cinepilot/app.py`
- Modify: `scripts/inspect_telemetry.py`
- Modify: `scripts/inspect_controls.py`
- Add or modify focused helper modules under `src/ats_cinepilot/bridge/` or `src/ats_cinepilot/ops/`
- Test: `tests/test_config_loading.py`
- Test: new diagnostics tests if behavior changes are isolated enough

- [ ] **Step 1: Write failing tests for selected live-path validation behavior**
Examples:
```python
def test_validate_runtime_config_rejects_live_mode_without_live_requirements():
    ...
```

- [ ] **Step 2: Run targeted tests to verify failure**
Run: `pytest tests/test_config_loading.py -q`
Expected: FAIL for missing live-path validation or diagnostics formatting.

- [ ] **Step 3: Implement minimal live-path selection and startup diagnostics**

- [ ] **Step 4: Re-run targeted tests**
Run: `pytest tests/test_config_loading.py -q`
Expected: PASS

- [ ] **Step 5: Commit**
Run: `git commit -m "feat: [live-shadow] 라이브 probe와 시작 진단 강화"`

### Task 3: Local Validation Attempt And Docs Sync

**Files:**
- Modify: `docs/IMPLEMENTATION_STATUS.md`
- Modify: `docs/TASK_BOARD.md`
- Modify: `docs/LOCAL_SETUP.md`
- Modify: `docs/RUNBOOK.md`
- Modify: `README.md`

- [ ] **Step 1: Run full verification**
Run:
```powershell
.\.venv\Scripts\python -m pytest -q
.\.venv\Scripts\python -m ruff check .
.\.venv\Scripts\ats-cinepilot check-config --config configs/profiles/replay_demo.yaml
.\.venv\Scripts\ats-cinepilot run --config configs/profiles/replay_demo.yaml --mode shadow --steps 5
.\.venv\Scripts\python scripts/inspect_telemetry.py --config <live-config> --frames 1
.\.venv\Scripts\python scripts/inspect_controls.py --config <live-config> --dry-run
```

- [ ] **Step 2: Update docs with exact local findings**

- [ ] **Step 3: Commit**
Run: `git commit -m "docs: [live-shadow] 실제 검증 결과 반영"`

- [ ] **Step 4: Push branch and open PR**
Expected: one reviewable PR against `main`, not merged.
