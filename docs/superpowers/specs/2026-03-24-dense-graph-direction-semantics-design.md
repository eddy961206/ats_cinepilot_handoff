# Dense Graph Direction Semantics Design

## Context

This session starts from merged `main`, not from a stacked PR base.

- PR #5 is merged into `main`
- PR #6 is merged into `main`
- base commit for this session is `main@7eef526`

Current project state:

- `shared_memory_v2` telemetry ingest works
- absolute pose contract remains:
  - `285:f64 -> world_x`
  - `293:f64 -> world_y`
  - `301:f64 -> world_z`
- coarse real graph path exists
- dense local ATS road GeoJSON path exists
- dense local graph now defaults to forward-only edges
- replay A/B showed:
  - straight/light-turn can expose `heading≈pi` mismatch
  - turn-heavy can improve route confidence while still failing on `MATCH_LOST`

The current stage is still Stage B: graph alignment and graph semantics.

## Problem

The matcher currently does not explain direction-aware failures well enough to tell whether the main remaining issue is:

1. edge direction semantics in the dense local graph,
2. heading cost design,
3. candidate selection logic,
4. or direct yaw uncertainty.

The current logs expose top-level metrics like `match`, `route`, `cte`, `candidate_count`, and `graph_failure_reason`, but they do not expose:

- the per-candidate direction relationship to vehicle heading,
- why a specific candidate won,
- whether a winner was selected because of distance, heading, continuity, or fallback,
- when the matcher is actually uncertain versus confidently wrong.

Without those diagnostics, changing matcher behavior would be guesswork.

## Goal

Improve dense local graph direction-semantics observability and make one conservative matcher update that materially improves turn-heavy replay behavior without:

- re-enabling synthetic reverse edges globally,
- broadening scope into route source integration,
- or making claims about ATS-wide route following.

Success criteria for this session:

- baseline replay behavior is reproduced from current docs,
- per-candidate direction diagnostics become reviewable from logs/artifacts,
- at least one evidence-backed matcher change lands,
- turn-heavy replay materially improves in either:
  - lower `MATCH_LOST` count,
  - later first `MATCH_LOST`,
  - or more explainable graph failure behavior,
- next dominant bottleneck is explicitly identified.

## Constraints

- Do not change the telemetry pose contract unless new evidence clearly disproves it.
- Do not promote `309:f32` to authoritative yaw without strong new proof.
- Do not add HUD route-source work unless graph-side direction semantics unexpectedly becomes good enough.
- Do not re-enable synthetic reverse edges as the selected default.
- Keep coarse graph and toy graph paths available for A/B comparison.
- Keep changes conservative and observable.

## Selected Approach

Use a three-part approach:

1. Reproduce the documented replay baseline exactly.
2. Add detailed direction-semantics diagnostics to the matcher and summary workflow.
3. Make a conservative matcher scoring update based on evidence from those diagnostics.

This is preferred over:

- global reverse-edge reintroduction, which hides the direction problem,
- or direct-yaw-first work, which is still downstream of unresolved graph semantics.

## Design

### 1. Baseline Reproduction

Before changing matcher behavior, rerun the documented baseline with:

- coarse real graph
- dense local forward-only graph
- straight/light-turn replay
- turn-heavy replay

Artifacts must include:

- shadow logs,
- summary JSON,
- exact commands used,
- and confirmation that the baseline pattern still holds.

The baseline pattern to confirm is:

- dense forward-only graph improves route confidence,
- straight/light-turn can still show `heading≈pi` mismatch,
- turn-heavy still degrades via `MATCH_LOST`.

### 2. Direction-Semantics Diagnostics

Extend matcher/runtime diagnostics so each step can expose more than the final winner.

For the top candidate edges, log:

- `edge_id`
- `start_node_id`
- `end_node_id`
- `distance_m`
- `edge_heading_rad`
- `vehicle_heading_rad`
- `signed_heading_delta_rad`
- direction classification:
  - `aligned`
  - `opposed`
  - `ambiguous`
- score breakdown:
  - distance component
  - heading component
  - continuity component
  - fallback component

For the selected winner, log:

- `selected_edge_id`
- `selected_reason`
  - `distance`
  - `heading`
  - `continuity`
  - `fallback`
- `direction_confidence_state`
  - `confident`
  - `ambiguous`
  - `opposed_best_available`

These diagnostics should be available both:

- in step logs / recorder rows,
- and in a saved machine-readable artifact like JSON or CSV.

### 3. Failure Taxonomy

Use the diagnostics to classify failures into explicit graph-side categories:

- `geometry_opposed_to_travel`
- `heading_cost_overpenalized_correct_edge`
- `nearest_geometry_beats_plausible_direction`
- `low_speed_heading_ambiguity`
- `turn_transition_heading_flip`
- `continuity_break`

Not every run must hit every category, but the analysis workflow should make it possible to assign observed failures to one of these categories.

### 4. Conservative Matcher Update

After the diagnostics reveal the dominant failure pattern, make one conservative matcher update.

Allowed update directions:

- signed heading penalty refinement
- low-speed ambiguity softening
- continuity-aware candidate preference
- candidate pruning for clearly opposed direction
- explicit ambiguous-direction state instead of hard choosing a bad edge

Not allowed as the selected default:

- global reverse-edge fallback
- opaque magic-constant stacking with no diagnostics

The preferred update order is:

1. improve candidate diagnostics and score breakdown,
2. reduce overconfident bad selections in ambiguous phases,
3. prefer physically plausible continuity when heading is uncertain.

### 5. Validation Strategy

Run A/B again after the matcher update with:

- coarse real graph
- dense local forward-only graph baseline artifact
- dense local forward-only graph after changes

Compare:

- `steps`
- `safety distribution`
- `first_MATCH_LOST_step`
- `first_ROUTE_CONFIDENCE_LOW_step`
- `match_confidence min/max`
- `route_confidence min/max`
- `cross_track_error max`
- `nearest_edge_distance range`
- `candidate_count range`
- `graph_failure_reasons`
- `heading_source distribution`
- new direction diagnostics

If ATS is running:

- rerun live `shared_memory_v2` probe
- run one fresh dense-local live shadow sample

If ATS is not running:

- document that live validation was not available
- do not overclaim beyond replay evidence

## File-Level Plan

Expected files to modify:

- `src/ats_cinepilot/map/matcher.py`
  - direction-aware scoring and candidate diagnostics
- `src/ats_cinepilot/app.py`
  - step log / recorder integration for new matcher diagnostics
- `scripts/summarize_shadow_log.py`
  - summary support for new direction fields
- `tests/test_matcher.py`
  - matcher diagnostics and score behavior
- `tests/test_shadow_log_summary.py`
  - new summary fields
- `docs/IMPLEMENTATION_STATUS.md`
- `docs/TASK_BOARD.md`
- `docs/RUNBOOK.md`
- `README.md`

Possible new helper script if needed:

- `scripts/analyze_match_direction_diagnostics.py`

Only add this if the existing summary tooling cannot express the needed review artifact cleanly.

## Risks

- The dense local graph may contain feature directions that are fundamentally unsuitable as-is, making matcher-only tuning insufficient.
- Low-speed ambiguity handling can reduce false penalties but also make selection less decisive.
- Diagnostics can become noisy if too many candidates are logged without filtering.

## Non-Goals

- Route source integration
- HUD parsing work
- Control sink work
- Active Mode
- ML/CV lane modeling
- ATS-wide graph correctness claims

## Expected Decision At End Of Session

The end of the session must make one explicit call:

- edge direction semantics still dominates,
- heading cost / candidate selection now dominates,
- direct yaw uncertainty is next,
- or some newly discovered bottleneck dominates.

Route source absence should only become the next step if graph-side matching becomes convincingly good, which is not the expected outcome for this session.
