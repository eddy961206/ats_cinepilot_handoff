# Dense Regional ATS Graph Next Bottleneck Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add one dense local ATS regional graph export path, run A/B comparisons against toy/coarse graph paths, and make an explicit call on whether graph fidelity or route source is the next main bottleneck.

**Architecture:** Use the local `trucksim_maps_repo` parser and graph generator against the installed ATS directory, then convert the resulting dense local graph plus parser node coordinates into the repo’s internal graph cache format. Keep toy and coarse public graph paths intact, expose dense graph selection with explicit config and metadata, and compare all graph paths through the existing shadow/replay summary workflow.

**Tech Stack:** Python 3.11, pytest, ruff, local Node/npm toolchain, `_ext/trucksim_maps_repo`, ATS `shared_memory_v2`

---

## Chunk 1: Dense Local Export Tooling

### Task 1: Add local dense graph adapter and metadata model

**Files:**
- Create: `src/ats_cinepilot/map/adapters/trucksim_dense.py`
- Modify: `src/ats_cinepilot/map/cache.py`
- Modify: `src/ats_cinepilot/map/graph.py`
- Test: `tests/test_trucksim_dense_graph.py`

- [ ] **Step 1: Write the failing adapter tests**

Add tests that:
- load a minimal `usa-graph.json` style payload and matching `usa-nodes.json`
- reconstruct internal nodes and directed edges
- preserve graph metadata for source/toolchain/crop region/export timestamp

- [ ] **Step 2: Run the targeted test to verify it fails**

Run:

```powershell
.\.venv\Scripts\python -m pytest -q tests\test_trucksim_dense_graph.py
```

Expected:
- import failure or missing adapter behavior

- [ ] **Step 3: Implement the dense graph adapter**

Implement a loader that:
- reads generator `usa-graph.json`
- reads parser `usa-nodes.json`
- reconstructs internal `RoadGraph`
- stores metadata:
  - `graph_source`
  - `alignment_mode`
  - `export_toolchain`
  - `source_input`
  - `export_timestamp_utc`
  - `crop_center_x_m`
  - `crop_center_z_m`
  - `crop_radius_m`

- [ ] **Step 4: Run the targeted test to verify it passes**

Run:

```powershell
.\.venv\Scripts\python -m pytest -q tests\test_trucksim_dense_graph.py
```

Expected:
- PASS

- [ ] **Step 5: Commit**

```powershell
git add src/ats_cinepilot/map/adapters/trucksim_dense.py src/ats_cinepilot/map/cache.py src/ats_cinepilot/map/graph.py tests/test_trucksim_dense_graph.py
git commit -m "feat: [map] dense local graph adapter 추가"
```

### Task 2: Add repeatable local export script

**Files:**
- Create: `scripts/export_dense_local_map.py`
- Modify: `scripts/export_map.py`
- Test: `tests/test_export_dense_local_map.py`

- [ ] **Step 1: Write the failing export-script tests**

Add tests that:
- validate command assembly for parser and graph generator
- validate metadata stamping and output path selection
- validate failure on missing parser/graph output files

- [ ] **Step 2: Run the targeted tests to verify they fail**

Run:

```powershell
.\.venv\Scripts\python -m pytest -q tests\test_export_dense_local_map.py
```

Expected:
- missing script/function failures

- [ ] **Step 3: Implement the export script**

The script should:
- accept ATS install dir, ext toolchain repo path, parser output dir, graph output dir, cache output path
- optionally reuse existing parser output
- run local parser
- run local graph generator
- convert and crop to internal graph cache
- fail loudly with the exact missing command/file when export breaks

- [ ] **Step 4: Run the targeted tests to verify they pass**

Run:

```powershell
.\.venv\Scripts\python -m pytest -q tests\test_export_dense_local_map.py
```

Expected:
- PASS

- [ ] **Step 5: Commit**

```powershell
git add scripts/export_dense_local_map.py scripts/export_map.py tests/test_export_dense_local_map.py
git commit -m "feat: [scripts] dense local graph export workflow 추가"
```

## Chunk 2: Runtime Selection and Diagnostics

### Task 3: Add dense graph runtime config and diagnostics buckets

**Files:**
- Create: `configs/live_probe_ats_dense_graph.yaml`
- Modify: `src/ats_cinepilot/app.py`
- Modify: `scripts/summarize_shadow_log.py`
- Modify: `tests/test_shadow_log_summary.py`
- Modify: `tests/test_startup.py`

- [ ] **Step 1: Extend tests for dense config/summary output**

Add tests that:
- startup summary includes the dense graph config identity
- shadow summary surfaces first `ROUTE_CONFIDENCE_LOW`
- graph failure and heading source distributions still serialize cleanly

- [ ] **Step 2: Run targeted tests to verify they fail**

Run:

```powershell
.\.venv\Scripts\python -m pytest -q tests\test_shadow_log_summary.py tests\test_startup.py
```

Expected:
- missing fields or config expectations

- [ ] **Step 3: Implement dense config and summary fields**

Update runtime so dense graph runs explicitly expose:
- dense graph source name
- alignment mode
- first `ROUTE_CONFIDENCE_LOW`
- existing graph diagnostics without breaking toy/coarse flows

- [ ] **Step 4: Run targeted tests to verify they pass**

Run:

```powershell
.\.venv\Scripts\python -m pytest -q tests\test_shadow_log_summary.py tests\test_startup.py
```

Expected:
- PASS

- [ ] **Step 5: Commit**

```powershell
git add configs/live_probe_ats_dense_graph.yaml src/ats_cinepilot/app.py scripts/summarize_shadow_log.py tests/test_shadow_log_summary.py tests/test_startup.py
git commit -m "feat: [runtime] dense graph 선택과 비교 진단 추가"
```

## Chunk 3: Dense Graph Export and Validation

### Task 4: Produce dense regional cache and validate export

**Files:**
- Create: `data/maps/cache/ats_usa_region_dense_graph_8km.json`
- Modify: `docs/SHARED_MEMORY_V2_DESIGN.md`
- Modify: `docs/RUNBOOK.md`

- [ ] **Step 1: Build the local parser if needed**

Run from the external repo:

```powershell
npm install
npm run build -w packages/clis/parser
```

Expected:
- parser build completes

- [ ] **Step 2: Run the dense export workflow**

Run:

```powershell
.\.venv\Scripts\python scripts\export_dense_local_map.py --ats-dir "D:\Steam\steamapps\common\American Truck Simulator" --toolchain-dir "C:\workspaces\python_workspace\_ext\trucksim_maps_repo" --parser-output "data\maps\trucksim_parser\ats_local" --graph-output "data\maps\trucksim_graph\ats_local" --cache-output "data\maps\cache\ats_usa_region_dense_graph_8km.json" --center-from-config configs\live_probe_moza_shared_memory.yaml --crop-radius-m 8000 --reuse-parser-output
```

Expected:
- parser output exists
- graph output exists
- dense cache written with metadata

- [ ] **Step 3: Inspect the dense cache metadata**

Run a short inspection command and confirm:
- node count is materially above the coarse public graph path
- graph source/toolchain/export timestamp are present
- crop center and radius match the current ATS area

- [ ] **Step 4: Commit**

```powershell
git add data/maps/cache/ats_usa_region_dense_graph_8km.json docs/SHARED_MEMORY_V2_DESIGN.md docs/RUNBOOK.md
git commit -m "feat: [data] dense regional graph cache와 export 메타데이터 추가"
```

## Chunk 4: A/B Comparison and Bottleneck Decision

### Task 5: Run dense graph A/B comparisons and update status docs

**Files:**
- Modify: `docs/IMPLEMENTATION_STATUS.md`
- Modify: `docs/TASK_BOARD.md`
- Modify: `README.md`

- [ ] **Step 1: Run replay smoke and live probe**

Run:

```powershell
.\.venv\Scripts\python -m pytest -q
.\.venv\Scripts\python -m ruff check .
.\.venv\Scripts\python scripts\inspect_telemetry.py --config configs\live_probe_ats_dense_graph.yaml --frames 3
```

Expected:
- tests pass
- lint passes
- dense config probe decodes live telemetry

- [ ] **Step 2: Run A/B comparisons**

At minimum compare straight/light-turn and turn-heavy samples across:
- toy graph
- coarse public graph
- dense local graph

Use existing replay conversion paths where possible so driver variance stays low.

- [ ] **Step 3: Summarize and decide the next bottleneck**

Run:

```powershell
.\.venv\Scripts\python scripts\summarize_shadow_log.py --input <toy_log> --input <coarse_log> --input <dense_log> --json data\debug\dense_graph_ab_summary.json
```

Then make one explicit decision:
- graph fidelity still dominant
- route source now dominant
- heading semantics still dominant

- [ ] **Step 4: Update docs to match reality**

Update status docs with:
- exact base used for this session
- selected local export toolchain
- dense graph export artifact path
- dense-vs-coarse comparison numbers
- explicit next-session recommendation:
  - route source
  - or more graph work

- [ ] **Step 5: Commit**

```powershell
git add docs/IMPLEMENTATION_STATUS.md docs/TASK_BOARD.md README.md
git commit -m "docs: [status] dense graph 비교와 다음 bottleneck 결론 반영"
```

## Chunk 5: Final Verification and PR

### Task 6: Final verification and PR preparation

**Files:**
- Review only unless fixes are needed

- [ ] **Step 1: Run final full verification**

```powershell
.\.venv\Scripts\python -m pytest -q
.\.venv\Scripts\python -m ruff check .
@'
from ats_cinepilot.ops.config import resolve_config, validate_runtime_config
from ats_cinepilot.ops.startup import validate_startup_requirements
for path in ['configs/profiles/replay_demo.yaml', 'configs/live_probe_ats_real_graph.yaml', 'configs/live_probe_ats_dense_graph.yaml']:
    cfg = resolve_config([path])
    issues = validate_runtime_config(cfg)
    issues.extend(validate_startup_requirements(cfg, mode='shadow'))
    print(path)
    if issues:
        print('config validation FAILED')
        for issue in issues:
            print('-', issue)
        raise SystemExit(1)
    print('config loaded OK')
    print('config validation OK')
'@ | .\.venv\Scripts\python -
```

Expected:
- all pass

- [ ] **Step 2: Push branch and open PR**

PR title:

```text
[codex] validate dense regional ATS graph and determine next bottleneck
```

- [ ] **Step 3: Include exact evidence in PR body**

Required sections:
- Goal
- Scope
- Base branch / repo state used
- Selected map/export toolchain
- What changed
- Alignment strategy
- Verification performed
- A/B comparison
- Dominant remaining bottleneck
- What remains unverified
- Risks
- Rollback
- Exact next human action

- [ ] **Step 4: Do not merge**

Leave the branch and PR reviewable for the next agent/human.
