# Dense Graph Direction Semantics Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reproduce the current dense-local replay baseline, add direction-semantics diagnostics, make one conservative matcher update, and determine whether turn-heavy failures are still dominated by graph direction semantics or by matcher heading/candidate selection behavior.

**Architecture:** Keep the current telemetry and graph contracts intact, especially the forward-only dense local graph. Extend matcher diagnostics rather than hiding failures. Use those diagnostics to drive one conservative matcher-scoring change, then rerun coarse-vs-dense A/B and, if ATS is running, one fresh live dense-local shadow sample.

**Tech Stack:** Python 3.11, pytest, ruff, ATS `shared_memory_v2`, JSONL recorder logs, local shadow replay configs

---

## Chunk 1: Baseline Reproduction

### Task 1: Reproduce the documented coarse-vs-dense baseline before code changes

**Files:**
- Review only: `docs/IMPLEMENTATION_STATUS.md`
- Review only: `docs/RUNBOOK.md`
- Artifact: `data/debug/dense_direction_baseline_summary.json`

- [ ] **Step 1: Verify the working tree is clean before baseline runs**

Run:

```powershell
git status --short --branch
```

Expected:
- only spec/plan commits present
- no uncommitted code changes

- [ ] **Step 2: Run replay smoke to confirm the baseline runtime still works**

Run:

```powershell
.\.venv\Scripts\ats-cinepilot run --config configs\profiles\replay_demo.yaml --mode shadow --steps 5
```

Expected:
- startup summary prints
- step loop completes

- [ ] **Step 3: Re-run coarse straight/light-turn baseline**

Create a temp overlay that writes to a dedicated verification log, then run:

```powershell
.\.venv\Scripts\ats-cinepilot run --config configs\live_probe_ats_real_graph.yaml --config configs\profiles\replay_ab_straight_light_turn.yaml --config configs\profiles\replay_ab_quiet.yaml --config <temp-overlay> --mode shadow
```

Expected:
- dedicated coarse straight baseline log written

- [ ] **Step 4: Re-run dense straight/light-turn baseline**

Run:

```powershell
.\.venv\Scripts\ats-cinepilot run --config configs\live_probe_ats_dense_local_graph.yaml --config configs\profiles\replay_ab_straight_light_turn.yaml --config configs\profiles\replay_ab_quiet.yaml --config <temp-overlay> --mode shadow
```

Expected:
- dedicated dense straight baseline log written

- [ ] **Step 5: Re-run coarse turn-heavy baseline**

Run:

```powershell
.\.venv\Scripts\ats-cinepilot run --config configs\live_probe_ats_real_graph.yaml --config configs\profiles\replay_ab_turn_heavy.yaml --config configs\profiles\replay_ab_quiet.yaml --config <temp-overlay> --mode shadow
```

Expected:
- dedicated coarse turn baseline log written

- [ ] **Step 6: Re-run dense turn-heavy baseline**

Run:

```powershell
.\.venv\Scripts\ats-cinepilot run --config configs\live_probe_ats_dense_local_graph.yaml --config configs\profiles\replay_ab_turn_heavy.yaml --config configs\profiles\replay_ab_quiet.yaml --config <temp-overlay> --mode shadow
```

Expected:
- dedicated dense turn baseline log written

- [ ] **Step 7: Summarize the reproduced baseline**

Run:

```powershell
.\.venv\Scripts\python scripts\summarize_shadow_log.py --input <coarse-straight-log> --input <dense-straight-log> --input <coarse-turn-log> --input <dense-turn-log> --json data\debug\dense_direction_baseline_summary.json
```

Expected:
- summary JSON saved
- baseline pattern matches docs:
  - dense forward-only straight run exposes heading mismatch
  - dense forward-only turn-heavy run still degrades via `MATCH_LOST`

- [ ] **Step 8: Commit the baseline artifact notes if docs/scripts changed**

```powershell
git add data/debug/dense_direction_baseline_summary.json
git commit -m "test: [baseline] dense direction baseline 재현"
```

Only commit if a tracked artifact or helper file changed. If no tracked file changed, skip commit.

## Chunk 2: Direction Diagnostics

### Task 2: Add matcher candidate direction diagnostics and tests

**Files:**
- Modify: `src/ats_cinepilot/map/matcher.py`
- Modify: `tests/test_matcher.py`

- [ ] **Step 1: Write failing tests for direction diagnostics**

Add tests that assert:
- top candidate diagnostics include edge id, distance, edge heading, vehicle heading, signed heading delta
- candidates are classified as `aligned`, `opposed`, or `ambiguous`
- winner diagnostics include score breakdown and selected reason

- [ ] **Step 2: Run the targeted matcher tests to verify they fail**

Run:

```powershell
.\.venv\Scripts\python -m pytest -q tests\test_matcher.py
```

Expected:
- failing assertions for new diagnostics

- [ ] **Step 3: Implement candidate direction diagnostics in the matcher**

Implement:
- richer `MatchDiagnostics`
- per-candidate diagnostic rows for the top N candidates
- winner score breakdown
- selected reason field
- direction confidence state

Keep the matcher conservative:
- no global reverse-edge fallback
- no hidden threshold explosion

- [ ] **Step 4: Re-run matcher tests**

Run:

```powershell
.\.venv\Scripts\python -m pytest -q tests\test_matcher.py
```

Expected:
- PASS

- [ ] **Step 5: Commit**

```powershell
git add src/ats_cinepilot/map/matcher.py tests/test_matcher.py
git commit -m "feat: [matcher] 방향 진단 정보 추가"
```

### Task 3: Surface diagnostics through recorder/log summary

**Files:**
- Modify: `src/ats_cinepilot/app.py`
- Modify: `scripts/summarize_shadow_log.py`
- Modify: `tests/test_shadow_log_summary.py`

- [ ] **Step 1: Extend summary tests with direction fields**

Add tests that assert summary parsing can handle:
- selected candidate reason
- direction confidence state
- top candidate direction classifications
- first `ROUTE_CONFIDENCE_LOW` still preserved

- [ ] **Step 2: Run targeted summary tests to verify they fail**

Run:

```powershell
.\.venv\Scripts\python -m pytest -q tests\test_shadow_log_summary.py
```

Expected:
- failing assertions for new status fields

- [ ] **Step 3: Write recorder/log integration**

Update runtime so recorder status includes:
- selected edge id
- selected reason
- direction confidence state
- candidate diagnostics snapshot

Update summary script so it can:
- keep existing headline metrics
- add direction-related counts/artifacts without breaking old logs

- [ ] **Step 4: Re-run summary tests**

Run:

```powershell
.\.venv\Scripts\python -m pytest -q tests\test_shadow_log_summary.py
```

Expected:
- PASS

- [ ] **Step 5: Commit**

```powershell
git add src/ats_cinepilot/app.py scripts/summarize_shadow_log.py tests/test_shadow_log_summary.py
git commit -m "feat: [logging] 방향 진단 로그와 요약 추가"
```

## Chunk 3: Matcher Update

### Task 4: Implement one conservative direction-aware matcher improvement

**Files:**
- Modify: `src/ats_cinepilot/map/matcher.py`
- Modify: `tests/test_matcher.py`

- [ ] **Step 1: Add failing behavior tests for the chosen matcher fix**

Write one or more tests that prove the desired conservative behavior, for example:
- low-speed ambiguity does not overcommit to a clearly opposed edge
- continuity can beat pure distance when heading is uncertain
- clearly opposed edges are penalized more than ambiguous edges

- [ ] **Step 2: Run the targeted matcher tests to verify they fail**

Run:

```powershell
.\.venv\Scripts\python -m pytest -q tests\test_matcher.py
```

Expected:
- new tests fail before the fix

- [ ] **Step 3: Implement the smallest evidence-backed matcher change**

Possible implementation directions:
- signed heading penalty refinement
- low-speed ambiguity soft handling
- continuity-aware score boost
- candidate pruning for strongly opposed direction

Do not:
- re-enable synthetic reverse edges globally
- introduce undocumented magic constants

- [ ] **Step 4: Re-run the matcher tests**

Run:

```powershell
.\.venv\Scripts\python -m pytest -q tests\test_matcher.py
```

Expected:
- PASS

- [ ] **Step 5: Commit**

```powershell
git add src/ats_cinepilot/map/matcher.py tests/test_matcher.py
git commit -m "fix: [matcher] 방향 선택 점수 보정"
```

## Chunk 4: Post-Change Validation

### Task 5: Re-run dense-local A/B with the new matcher behavior

**Files:**
- Artifact: `data/debug/dense_direction_postchange_summary.json`

- [ ] **Step 1: Re-run the same four replay cases**

Run the same commands as baseline for:
- coarse straight/light-turn
- dense straight/light-turn
- coarse turn-heavy
- dense turn-heavy

Write to fresh verify log paths.

- [ ] **Step 2: Summarize post-change runs**

Run:

```powershell
.\.venv\Scripts\python scripts\summarize_shadow_log.py --input <coarse-straight-log> --input <dense-straight-log> --input <coarse-turn-log> --input <dense-turn-log> --json data\debug\dense_direction_postchange_summary.json
```

Expected:
- post-change summary saved

- [ ] **Step 3: Compare baseline vs post-change**

Record at minimum:
- safety distribution
- first `MATCH_LOST`
- first `ROUTE_CONFIDENCE_LOW`
- match min/max
- route min/max
- cte max
- nearest-edge range
- candidate-count range
- graph failure reasons
- direction diagnostics distribution

- [ ] **Step 4: Commit tracked artifacts only if any tracked file changed**

```powershell
git add data/debug/dense_direction_postchange_summary.json
git commit -m "test: [ab] 방향 matcher 변경 후 비교 추가"
```

Only commit if a tracked artifact or helper file changed. If no tracked file changed, skip commit.

### Task 6: Fresh live validation if ATS is running

**Files:**
- Review only unless docs/scripts need updates

- [ ] **Step 1: Probe live shared memory**

Run:

```powershell
.\.venv\Scripts\python scripts\inspect_telemetry.py --config configs\live_probe_ats_dense_local_graph.yaml --frames 3
```

Expected:
- either live telemetry is ready
- or ATS-not-running is stated clearly

- [ ] **Step 2: If ATS is running, run one dense-local live shadow sample**

Run:

```powershell
.\.venv\Scripts\ats-cinepilot run --config configs\live_probe_ats_dense_local_graph.yaml --mode shadow --steps 300
```

Expected:
- one fresh live sample if the environment allows it

- [ ] **Step 3: If ATS is not running, do not invent live conclusions**

Document replay-only validation for this session if no live run was possible.

## Chunk 5: Docs and PR

### Task 7: Update docs with baseline, diagnosis, and bottleneck decision

**Files:**
- Modify: `README.md`
- Modify: `docs/IMPLEMENTATION_STATUS.md`
- Modify: `docs/TASK_BOARD.md`
- Modify: `docs/SHARED_MEMORY_V2_DESIGN.md`
- Modify: `docs/RUNBOOK.md`

- [ ] **Step 1: Update the docs to match the new evidence**

Document:
- base used for the session
- baseline reproduction result
- added diagnostics
- conservative matcher update
- post-change A/B result
- whether live validation happened

- [ ] **Step 2: Make one explicit bottleneck decision**

Choose exactly one dominant remaining bottleneck:
- edge direction semantics
- heading cost / candidate selection
- direct yaw uncertainty
- route source absence
- something else

- [ ] **Step 3: Re-run full verification**

Run:

```powershell
.\.venv\Scripts\python -m pytest -q
.\.venv\Scripts\python -m ruff check .
.\.venv\Scripts\ats-cinepilot run --config configs\profiles\replay_demo.yaml --mode shadow --steps 5
```

Expected:
- all pass

- [ ] **Step 4: Commit docs**

```powershell
git add README.md docs/IMPLEMENTATION_STATUS.md docs/TASK_BOARD.md docs/SHARED_MEMORY_V2_DESIGN.md docs/RUNBOOK.md
git commit -m "docs: [status] 방향 semantics 검증 결과 반영"
```

### Task 8: Push and open the PR

**Files:**
- Review only

- [ ] **Step 1: Push branch**

```powershell
git push -u origin codex/dense-graph-direction-semantics
```

- [ ] **Step 2: Open the PR**

Title:

```text
[codex] improve dense graph direction semantics and matcher heading selection
```

Required PR body sections:
- Goal
- Scope
- Base branch / repo state used
- Baseline reproduced
- Direction-semantics diagnosis
- What changed
- Why these changes were chosen
- Verification performed
- A/B comparison
- Dominant remaining bottleneck
- What remains unverified
- Risks
- Rollback
- Exact next human action

- [ ] **Step 3: Do not merge**

Leave the branch and PR reviewable for the next human/agent.
