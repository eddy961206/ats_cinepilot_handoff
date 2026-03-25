# Constrained Live Active ATS Demo Design

Base lineage for this spec: `codex/dense-graph-direction-semantics@1ed1e75`

## Goal

Build the first tightly constrained ATS live active demo:

- real `shared_memory_v2` telemetry
- real control sink writes through `Local\SCSControls`
- one explicit low-speed corridor only
- hard demo safety cage
- explicit operator workflow and disengage path

This is a demo milestone, not a claim of general active autonomy.

## Scope

In scope:

- make the control sink path real on this Windows machine
- add explicit control preflight and micro-probe tooling
- choose one known-good demo corridor and freeze it in config
- add a demo-only runtime guard that refuses control outside corridor bounds
- add operator scripts/docs for a short live active demo

Out of scope:

- broader route following
- dense-graph generalization
- HUD route source work
- control plugin redesign
- Active Mode beyond the demo corridor

## Selected Demo Path

### Telemetry

- Source: `shared_memory_v2`
- Contract:
  - `285:f64 -> world_x`
  - `293:f64 -> world_y`
  - `301:f64 -> world_z`
- Pose frame: `anchored_local`

### Graph / corridor

Use the existing `data/maps/cache/default_graph.json` toy graph on the known stable bring-up path.

Why:

- it already produced ATS-backed shadow runs with long `NONE` stretches
- it avoids the current dense-graph direction/topology bottleneck
- it is the narrowest honest slice for a first active demo

Corridor contract:

- graph source must be `toy_graph`
- alignment mode must be `anchored_local_toy_graph`
- approved edge IDs limited to `ab`
- progress bounds limited to the inner straight segment to avoid the `ab -> bc` transition
- low speed cap only

## Control Path

Use `ETS2LA/scs-sdk-controller` as the live control sink.

Machine facts already observed:

- telemetry plugin DLL exists in ATS
- `scs-sdk-controller` is not bundled in this repo
- the external repo can be built locally with Visual Studio 2022 Build Tools already on the machine
- `cmake.exe` exists inside the Build Tools install even though it is not on PATH

Repo-side contract:

- keep external control code outside this repo under `_ext/scs-sdk-controller`
- allow config-driven module search paths so the app can import `scscontroller.py` without vendoring it
- keep `noop` and `recording` sinks available

## Demo Safety Cage

Add a dedicated demo guard that only allows active writes when all are true:

- telemetry source is live, not replay
- control sink is healthy
- pose source is authoritative absolute
- anchor heading is locked
- no discontinuity/reset is active
- graph source and alignment mode match the demo contract
- matched edge is inside the approved corridor
- progress is inside approved bounds
- direction confidence is not ambiguous
- map match confidence exceeds the demo minimum
- cross-track error stays below the demo maximum
- heading error stays below the demo maximum
- nearest-edge distance stays below the demo maximum
- route confidence stays above the demo minimum
- graph failure reason is empty
- speed stays below the demo cap
- manual override flag is clear
- the demo has observed a short run of consecutive qualifying shadow frames before arming

When any condition fails:

- immediately write neutral control
- record the demo guard reason
- reset arming progress if the failure invalidates corridor trust

## Validation Strategy

1. Build and install the control plugin DLL into ATS.
2. Verify `inspect_controls.py --dry-run` can see module import + DLL path + mapping state.
3. Add explicit micro-probes for steering, throttle, and brake.
4. Run shadow on the demo corridor with the demo graph/cage config.
5. Run a short active attempt only after shadow qualification and micro-probes succeed.

## Risks

- physical manual override detection is still not authoritative; the demo must rely on `Ctrl+C`, ATS pause, and an explicit override flag as the immediate operator escape paths
- the toy-graph corridor is intentionally narrow and not representative of general road-following
- if the plugin loads but the game is not in a write-accepting state, control probes may appear healthy while the truck does not respond

## Expected Deliverables

- `configs/demo_active_corridor.yaml`
- control module search-path support
- control micro-probe path
- demo safety cage module and logging
- helper scripts for build/install/run/override
- docs updated with exact live demo commands and safety warnings
