# Dense Regional ATS Graph Next Bottleneck Design

**Date:** 2026-03-22  
**Repository Base:** `codex/real-ats-world-graph-alignment` @ `06d9b67`  
**Why this base:** PR #5 is still open, so this session must stack on the PR #5 head commit rather than stale `main`.

## Goal

Move the project from coarse real-graph bring-up to dense local regional graph validation, then use that denser graph to decide whether the next dominant bottleneck is still graph fidelity, missing route source, or telemetry heading semantics.

## Current State

Already in place:
- `shared_memory_v2` live telemetry ingest
- authoritative absolute pose contract
  - `285:f64 -> world_x`
  - `293:f64 -> world_y`
  - `301:f64 -> world_z`
- discontinuity detection and anchor reset
- toy graph bring-up path
- coarse public real-graph path based on `truckermudgeon/maps` `usa-graph-demo.json`
- A/B replay workflow between toy graph and coarse public graph

Current evidence says:
- telemetry ingest is real and stable enough for Stage B
- absolute pose can align to a real graph without undocumented transforms
- remaining failure is likely coarse graph fidelity and/or missing route intent

## Non-Goals

This session does not:
- touch Active Mode
- implement control plugin logic
- build wheel actuation
- add ML lane models
- claim production-quality ATS-wide route following
- promote `309:f32` to authoritative yaw without strong new evidence

## Approaches Considered

### Approach 1: Reuse another public graph artifact

Keep using public `truckermudgeon/maps` data and try a different pre-generated artifact.

Pros:
- fastest to wire
- least local tooling work

Cons:
- still likely coarse
- does not satisfy the session goal of a local dense regional graph
- weak evidence for deciding whether route source is now the next blocker

### Approach 2: Parse ATS `.scs` archives directly in Python

Build a new in-repo parser for game archives and sectors.

Pros:
- fully self-contained in Python

Cons:
- too large for this session
- high risk of derailing into parser work
- duplicates existing external tooling that already parses the same game data

### Approach 3: Use local `truckermudgeon/maps` parser + graph generator

Run the already cloned local `trucksim_maps_repo` against the installed ATS directory, keep one local parser output directory, then adapt the generated dense graph and parser node data into the repo’s internal graph cache format.

Pros:
- uses one concrete local toolchain only
- works from the user’s installed game data and DLC set
- gives denser local routing connectivity than the public demo graph
- preserves continuity with the coarse path already added in PR #5

Cons:
- requires Node/native parser execution
- adapter must understand graph-generator output plus parser node coordinates

## Selected Approach

Choose Approach 3.

Concrete toolchain:
- local source repo: `C:\workspaces\python_workspace\_ext\trucksim_maps_repo`
- ATS install input: `D:\Steam\steamapps\common\American Truck Simulator`
- raw parser output: local JSON files emitted by `packages/clis/parser`
- dense graph source: `packages/clis/generator commands/graph.ts` non-demo output

Rationale:
- it is the smallest path that can produce a denser local regional graph from the actual installed game and DLC set
- it avoids introducing a second unrelated map toolchain
- it allows a clean three-way comparison:
  - toy graph
  - coarse public graph
  - dense local regional graph

## Expected Source and Output Artifacts

### Selected source files

Input game files:
- `D:\Steam\steamapps\common\American Truck Simulator\base_map.scs`
- `D:\Steam\steamapps\common\American Truck Simulator\base.scs`
- installed ATS DLC `.scs` files in the same directory

Parser output directory:
- `data/maps/trucksim_parser/ats_local/`

Expected parser output files used by this session:
- `usa-nodes.json`
- `usa-roads.json`
- `usa-prefabs.json`
- `usa-prefabDescriptions.json`
- other graph-generator-required parser outputs

Focused GeoJSON output directory:
- `data/maps/trucksim_geojson/ats_local_region/`

Expected focused road artifact:
- `data/maps/trucksim_geojson/ats_local_region/*.geojson`

Internal runtime cache artifact:
- `data/maps/cache/ats_usa_region_dense_local_geojson_8km.json`

Dense runtime config:
- `configs/live_probe_ats_dense_local_graph.yaml`

The coarse path remains:
- `configs/live_probe_ats_real_graph.yaml`
- `data/maps/cache/ats_usa_region_real_graph_8km.json`

The toy path remains:
- `configs/live_probe_ats_toy_graph.yaml`

## Architecture

### 1. Local export layer

Add a repository script that orchestrates one local export flow:

1. run local `trucksim_maps` parser against the ATS install
2. run local `trucksim_maps` graph generator against the parser output
3. convert the dense graph plus parser node coordinates into the repo’s internal graph cache
4. crop to a telemetry-derived regional radius
5. stamp metadata for reproducibility

This keeps dense local export as a repeatable workflow rather than a one-off manual process.

### 2. Dense graph adapter layer

Add a new adapter path for local `trucksim_maps` dense graph output.

Responsibilities:
- read `usa-graph.json`
- read `usa-nodes.json` from the same parser directory
- reconstruct directed internal edges from generator neighbors
- preserve node coordinates from parser output
- preserve routing connectivity
- preserve metadata needed for diagnostics

This adapter must stay separate from the current public `demoGraph` adapter logic so the boundary between coarse and dense sources stays explicit.

### 3. Runtime graph selection layer

Keep graph paths explicit in config.

Required runtime configs:
- toy graph config
- coarse public graph config
- dense local graph config

The app already logs `graph_source`, `alignment_mode`, candidate count, nearest-edge distance, and graph failures. This session extends those diagnostics only if needed to distinguish:
- no nearby edge
- coverage gap
- ambiguous branching
- low route confidence

## Alignment Strategy

Default assumption remains unchanged:
- `285:f64 -> world_x`
- `293:f64 -> world_y`
- `301:f64 -> world_z`

For the dense local graph:
- use the same ATS coordinate space as parser node data
- prefer identity alignment with no undocumented transform
- if a transform is required, it must be documented in graph metadata and surfaced in config

Re-validation required:
- axis/sign correctness
- scale correctness
- crop center correctness
- regional cache actually covers the driven area

## Data Flow

1. ATS `shared_memory_v2` emits authoritative absolute pose.
2. Dense local export workflow builds a regional cache around the live ATS operating area.
3. Runtime loads one of:
   - toy graph
   - coarse public graph
   - dense local graph
4. Shadow runs emit:
   - graph source
   - alignment mode
   - candidate count
   - nearest-edge distance
   - graph failure reason
   - cross-track error
   - heading error
   - route confidence
5. A/B summary compares the three graph paths on the same replayed motion where possible.

## Failure Handling

### Export-time failures

- local Node toolchain missing
- parser build missing
- parser output incomplete
- graph generator output missing required files
- crop center unavailable from telemetry

Behavior:
- fail loudly
- report exact missing command/file
- do not silently fall back to coarse public graph when dense export was requested

### Runtime failures

- dense graph cache missing
- dense graph cache metadata inconsistent
- no nearby edge
- graph coverage gap
- route confidence low despite strong geometric match
- branching ambiguity with multiple plausible exits

Behavior:
- log explicit graph source and failure reason
- preserve safety disengagement rules
- do not claim route-following capability from geometry alone

## Testing and Verification

Minimum tests:
- adapter unit test for local dense graph conversion
- metadata round-trip test for export timestamp/toolchain/crop region
- config loading test for dense graph config
- summary logic test if new failure buckets are added

Required runtime verification this session:
- `pytest`
- lint
- replay smoke
- live `shared_memory_v2` probe
- dense graph export validation
- at least one A/B comparison that includes the dense local graph

Target validation set:
- straight/light-turn sample
- turn-heavy sample

Comparison axes:
- steps
- safety distribution
- first `MATCH_LOST`
- first `ROUTE_CONFIDENCE_LOW`
- match confidence range
- route confidence range
- cross-track error max
- nearest-edge distance range
- graph failure reasons
- heading source distribution

## Decision Rule for Next Session

At the end of this session, make one explicit call:

### A. Next bottleneck is still graph fidelity

Choose this if the dense local graph still materially improves geometry metrics, but branch intent and route confidence remain underconstrained because graph density/coverage is still insufficient.

### B. Next bottleneck is missing route source

Choose this if the dense local graph materially improves turn-heavy matching enough that route ambiguity, exits, and branch choice become the dominant remaining problem.

If B is selected, next session should prepare one narrow route-source path in this order:
1. existing HUD route hint path with one locked preset
2. stronger direct route access only if already available in the chosen toolchain

### C. Next bottleneck is still heading semantics

Choose this only if the dense graph removes graph-coarseness explanations but turn-heavy mismatch still clusters around heading behavior.

## Success Criteria

This session succeeds if it leaves:
- one dense local ATS regional graph path
- one explicit dense runtime config
- one reproducible dense export workflow
- one clean A/B comparison including the dense graph
- one explicit next-bottleneck decision between graph fidelity vs route source vs heading semantics

## Known Limitations

- `trucksim_maps` generated geometry may still be imperfect around complex intersections
- local export may depend on parser/generator build health
- this session still does not solve trustworthy branch intent by itself
- dense graph improvement alone is not proof of production route following
