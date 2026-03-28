# Roadmap

## Stage A — telemetry semantics

- shared_memory_v2 ingest
- absolute pose
- heading/discontinuity handling
- 상태: done enough for demos

## Stage B — graph semantics

- coarse graph
- dense local graph
- curated dense corridor
- 상태: enough for narrow demos, not general

## Stage C — constrained active demos

- C1. straight corridor active demo
  - done
- C2. gentle-curve toy corridor active demo
  - done
- C3. curated dense-corridor active demo
  - done
- C3.5. CV observer / overlay / safety observer layer
  - done enough for first live observer/demo artifacts
- C4. curated multi-edge dense corridor active demo
  - **current likely next stage**
- C5. constrained route-aware demo
  - later

## Current Hard Call

- next session should not pivot to CV-only control
- next session should likely be:
  - `C4 curated multi-edge dense corridor active demo`
  - with CV observer left on as observability/guard support
- route-aware demo is still later

## Stage D — broader shadow / active autonomy

- later
- explicitly out of scope right now
