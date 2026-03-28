# Curated Dense Corridor Active Demo Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** toy gentle-curve demo 다음 단계로, local dense graph에서 추출한 curated corridor 하나로 첫 denser-corridor live active demo를 만든다.

**Architecture:** source dense graph에서 oriented corridor subgraph와 corridor contract artifact를 만든다. runtime은 이 contract를 읽어 startup summary, demo cage, recorder diagnostics, runner command를 일관되게 적용한다. active authority는 approved corridor sequence 안에서만 허용한다.

**Tech Stack:** Python, PowerShell, existing ATS CinePilot runtime, pytest, ruff, GitHub CLI

---

## Chunk 1: Base, Spec, Baseline

### Task 1: main consolidation state를 확인하고 baseline evidence를 저장

**Files:**
- Create: `docs/ACTIVE_DEMO_EXPERIMENT_LOG.md`
- Modify: `docs/IMPLEMENTATION_STATUS.md`

- [ ] `git rev-parse main`와 `git rev-parse HEAD`로 base를 기록한다.
- [ ] gentle-curve readiness / runner baseline을 다시 실행한다.
- [ ] baseline command와 결과를 experiment log에 append한다.

### Task 2: dense corridor source sequence를 확정한다

**Files:**
- Modify: `docs/superpowers/specs/2026-03-28-curated-dense-active-demo-design.md`
- Create: `configs/corridors/demo_dense_curated_corridor.yaml`

- [ ] source dense graph에서 chosen traversal sequence와 start/end coordinates를 기록한다.
- [ ] corridor contract YAML 초안을 만든다.
- [ ] contract에 speed cap / threshold / ordered edge sequence를 넣는다.

## Chunk 2: Artifact and Runtime

### Task 3: failing tests를 먼저 추가한다

**Files:**
- Create: `tests/test_demo_corridor_contract.py`
- Modify: `tests/test_demo_cage.py`
- Modify: `tests/test_startup.py`

- [ ] corridor contract loading 테스트를 쓴다.
- [ ] demo cage가 ordered sequence regression / skip를 막는 테스트를 쓴다.
- [ ] startup summary가 corridor contract 정보를 노출하는 테스트를 쓴다.
- [ ] 새 테스트를 단독 실행해서 실패를 확인한다.

### Task 4: curated dense corridor artifact loader / exporter를 구현한다

**Files:**
- Create: `src/ats_cinepilot/ops/demo_corridor.py`
- Create: `scripts/export_demo_dense_corridor.py`
- Create: `data/maps/cache/demo_dense_curated_corridor_graph.json`

- [ ] contract loader를 추가한다.
- [ ] source dense graph에서 oriented subgraph를 뽑는 export 스크립트를 만든다.
- [ ] chosen corridor cache를 생성한다.
- [ ] contract loader / exporter 테스트를 통과시킨다.

### Task 5: demo cage와 startup/runtime를 corridor-aware로 확장한다

**Files:**
- Modify: `src/ats_cinepilot/safety/demo_cage.py`
- Modify: `src/ats_cinepilot/app.py`
- Modify: `src/ats_cinepilot/ops/startup.py`
- Modify: `src/ats_cinepilot/ops/config.py`

- [ ] demo config에서 corridor contract path를 읽게 한다.
- [ ] demo cage에 ordered sequence tracking을 추가한다.
- [ ] recorder/status log에 corridor index / sequence validity를 남긴다.
- [ ] startup summary에 corridor contract 이름과 graph source를 노출한다.
- [ ] 관련 테스트를 녹색으로 만든다.

## Chunk 3: Demo UX and Verification

### Task 6: dense corridor demo config / runner를 추가한다

**Files:**
- Create: `configs/demo_active_dense_corridor.yaml`
- Create: `scripts/run_demo_active_dense_corridor.ps1`
- Modify: `scripts/inspect_controls.py`
- Modify: `scripts/inspect_telemetry.py`

- [ ] gentle-curve config를 기반으로 dense corridor demo config를 만든다.
- [ ] readiness + shadow qualification + active run helper를 만든다.
- [ ] operator warnings와 log path를 명시한다.
- [ ] config validation이 통과하는지 확인한다.

### Task 7: docs를 현재 사실에 맞게 갱신한다

**Files:**
- Modify: `README.md`
- Modify: `docs/IMPLEMENTATION_STATUS.md`
- Modify: `docs/TASK_BOARD.md`
- Modify: `docs/RUNBOOK.md`
- Modify: `docs/ACTIVE_DEMO_EXPERIMENT_LOG.md`

- [ ] dense curated corridor의 목적과 한계를 문서에 반영한다.
- [ ] exact commands / safety bounds / known-good setup을 정리한다.
- [ ] next milestone이 무엇인지 명시한다.

### Task 8: full verification, PR, merge

**Files:**
- Modify: `.codex_pr_body.md`

- [ ] `pytest -q`
- [ ] `ruff check .`
- [ ] `ats-cinepilot check-config --config configs/demo_active_dense_corridor.yaml`
- [ ] replay smoke
- [ ] telemetry readiness
- [ ] control readiness
- [ ] gentle-curve baseline reproduction
- [ ] dense corridor shadow qualification
- [ ] dense corridor live active attempt
- [ ] `scripts/summarize_shadow_log.py`로 dense demo summary를 저장한다.
- [ ] PR body를 요구 섹션대로 작성한다.
- [ ] `gh pr create`
- [ ] 검증이 충분하면 `gh pr merge --merge --delete-branch`
