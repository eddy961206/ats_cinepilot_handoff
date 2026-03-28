# Curated Dense Corridor Active Demo Design

- Date: 2026-03-28
- Base decision: `main` was stale at `7eef526`; required lineage lived on `codex/real-ats-world-graph-alignment@86c3517`.
- Consolidation decision: merge integration lineage to `main` first, then branch from updated `main@880cfa5`.
- Working branch for implementation: `codex/dense-curated-active-demo`.

## Goal

Build the first live active ATS demo on a curated dense local corridor that is more realistic than the toy gentle-curve demo while preserving the same narrow, reviewable safety philosophy.

## Non-goals

- No general Active Mode.
- No route-following.
- No complex intersection handling.
- No CV or ML lane work.
- No broad dense-local active driving outside one curated corridor.

## Selected approach

Use a **curated dense subgraph** extracted from the existing local ATS dense graph cache instead of trying to drive the whole dense graph directly.

### Why this approach

1. It keeps the graph more realistic than the toy corridor because the source geometry comes from the exported ATS local graph.
2. It avoids reopening the unsolved dense-graph ambiguity problem because runtime matching only sees a short approved edge chain.
3. It keeps safety reviewable because the corridor contract can name exact edge IDs, direction, thresholds, and start assumptions.

## Corridor candidate

Use a short three-edge local-road chain extracted from `data/maps/cache/ats_usa_region_dense_local_geojson_8km.json`:

1. `62b6432dc234019road1__fwd`
2. `62b64329c433fe5__fwd`
3. `62b64321d733fe6__fwd`

Why this chain:

- forward-only and topologically connected
- low-road-class local geometry, appropriate for low-speed demoing
- total path length is about `136.4m`
- total heading change is about `21.5deg`, enough to create visible closed-loop steering
- internal transitions are singular in the extracted subgraph, so route ambiguity stays intentionally suppressed

## Runtime contract

Create a dedicated dense demo profile and runner:

- `configs/corridors/demo_dense_curated_corridor.yaml`
- `configs/demo_active_dense_corridor.yaml`
- `scripts/run_demo_active_dense_corridor.ps1`
- generated graph cache: `data/maps/cache/demo_dense_curated_corridor_graph.json`

The corridor contract should be explicit and human-readable. It should include:

- source graph/cache path
- curated edge sequence in order
- approved travel direction (`forward`)
- start edge ID
- start progress ceiling for arming/bootstrap
- max speed
- dense-corridor safety thresholds

## Safety model

Preserve the existing demo cage philosophy and tighten it for the curated dense corridor.

Allow active control only if all are true:

- telemetry healthy
- hybrid control sink healthy
- graph source and alignment mode match the curated dense demo
- current matched edge is inside the approved ordered edge sequence
- observed edge order never moves backward or skips unexpectedly
- start arming begins on the configured start edge within a small progress window
- no graph failure reason
- no discontinuity
- anchor locked
- heading source approved
- candidate count stays within corridor limit
- nearest-edge distance, match confidence, route confidence, cross-track error, heading error stay within dense-demo thresholds
- speed stays below the dense demo cap
- ATS focus remains active
- manual override remains available

On any failure:

- immediately neutralize control
- release held keys
- log disengage reason
- do not try to recover by relaxing thresholds

## Implementation outline

1. Add a small graph-extraction helper that writes a subgraph cache from an explicit edge sequence.
2. Add curated corridor config/artifact for the chosen dense chain.
3. Extend `DemoSafetyCage` with optional ordered-edge/start-window enforcement.
4. Add dense demo runner script and startup/logging summaries.
5. Add summary metrics for approved edge sequence adherence and non-trivial steering.
6. Verify gentle baseline first, then dense shadow qualification, then bounded live active demo.

## Verification plan

Required evidence before merge:

- `pytest`
- `ruff check .`
- config validation for dense demo config
- replay smoke
- telemetry readiness
- control readiness
- gentle-curve baseline reproduction
- dense shadow qualification on the curated corridor
- at least one real dense curated active demo attempt if ATS is available

## Expected hard call after session

If the curated dense demo succeeds, the next milestone should be a **slightly richer curated multi-edge corridor**, not general active driving. Route-aware work should only follow after the curated dense corridor remains stable enough that corridor semantics are no longer the dominant bottleneck.
