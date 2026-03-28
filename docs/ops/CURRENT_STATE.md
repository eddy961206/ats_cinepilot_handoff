# Current State

## Current Truth

- base branch for this session: `main@6eb557371a4806595f4e4fbfa0c28356367bcfd4`
- current working stage: `Stage C3.5`
  - dense curated corridor active demo exists
  - CV observer / overlay / guard layer now exists on top
  - durable in-repo ops handoff harness now exists
- primary planning/control path is still:
  - live telemetry
  - graph matcher
  - preview/speed planners
  - hybrid control sink
- CV is secondary only:
  - observer
  - overlay / explainability
  - disengage-only guard

## What Works

- `SCSTelemetrySharedv2_ats` live ingest works
- absolute pose contract `285/293/301` works
- steering / blinkers via module path work
- throttle / brake via keyboard path work
- straight constrained live active demo works
- gentle-curve constrained live active demo works
- curated dense-corridor constrained live active demo works
- live CV observer overlay works
- lane observer v1 works on live ATS capture
- CV artifact saving works
  - annotated frames
  - annotated MP4
  - machine-readable CV summary JSONL
- dense demo can run with CV enabled without replacing planner/control

## What Does Not

- module longitudinal is still not the usable live path
- dense corridor repeatability is not stable enough yet
- route-aware autonomy is still not implemented
- barrier / road-edge perception is not implemented yet
- live vehicle detection evidence is partial only
  - latest short dense+CV rerun had `lead_detected=2`
  - but confidence max was `0.567`, below the current guard threshold `0.60`
- lane guard is intentionally not trusted enough to arm by default in active demo configs yet
- current CV capture is monitor-region based, so ATS should stay maximized/full-screen for reliable overlays

## Current Primary Bottleneck

현재 병목은 general autonomy가 아니라:

1. dense curated corridor repeatability
2. demo-only longitudinal shaping
3. live vehicle / barrier CV evidence 부족
4. lead-vehicle guard threshold evidence 부족

즉 CV observer는 붙었지만, 다음 단계는 CV-only driving이 아니라 **repeatable curated corridor + richer live visual risk evidence**다.

## Last Reproduced Dense Baseline

command:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_demo_active_dense_corridor.ps1 -ShadowSteps 12 -ActiveSteps 140 -ActiveCountdownSeconds 3
```

latest baseline on `2026-03-29`:

- `steps=152`
- `safety={MATCH_LOST: 145, DEMO_GUARD: 7}`
- `first_MATCH_LOST=1`
- `match=[0.718, 1.000]`
- `route=[0.487, 0.694]`
- `cte_max=1.038`
- `cand=[1, 1]`
- `steering_abs_max=0.300`
- `non_trivial_steering_count=152`
- `throttle_command_count=33`
- `brake_command_count=108`

해석:

- dense demo helper / telemetry / control path는 살아 있다
- 하지만 truck placement / runtime fit / bootstrap 이후 drift 때문에 best run보다 훨씬 나빠질 수 있다
- 이 variability는 future session에서 반복 실험 대상으로 반드시 남겨야 한다

## Current CV Verification Snapshot

### observer-only live run

- command:
  - `powershell -ExecutionPolicy Bypass -File scripts\run_cv_observer_dense_corridor.ps1 -Steps 80`
- result:
  - `frames=80`
  - `lane_detected=80`
  - `lane_conf=[1.000, 1.000]`
  - `lead_detected=0`
  - `guard_reasons={none: 80}`
- artifacts:
  - `data/artifacts/cv/observer_dense_corridor/observer_overlay.mp4`
  - `data/artifacts/cv/observer_dense_corridor/frame_00001.jpg`
  - `data/logs/cv_observer_dense_corridor.cv.jsonl`

### dense active demo with CV

- command:
  - `powershell -ExecutionPolicy Bypass -File scripts\run_demo_active_dense_corridor_with_cv.ps1 -ShadowSteps 8 -ActiveSteps 80 -ActiveCountdownSeconds 3`
- result:
  - `steps=88`
  - `safety={MATCH_LOST: 17, ROUTE_CONFIDENCE_LOW: 2, DEMO_GUARD: 21, NONE: 48}`
  - `match=[0.700, 1.000]`
  - `route=[0.480, 0.700]`
  - `cte_max=0.039`
  - `steering_abs_max=0.300`
  - `non_trivial_steering_count=20`
  - `lane_detected=88`
  - `lead_detected=0`
- interpretation:
  - CV layer did not replace planner/control
  - CV overlay/artifacts were produced during live active demo
  - CV guard stayed quiet in this run because no lead-risk visual event was observed

### short dense active + CV rerun

- command:
  - `powershell -ExecutionPolicy Bypass -File scripts\run_demo_active_dense_corridor_with_cv.ps1 -ShadowSteps 4 -ActiveSteps 40 -ActiveCountdownSeconds 3`
- result:
  - `steps=44`
  - `safety={MATCH_LOST: 44}`
  - `cte_max=7.109`
  - `lane_detected=44`
  - `lead_detected=2`
  - `lead_conf=[0.385, 0.567]`
- interpretation:
  - dense active repeatability는 다시 흔들렸다
  - 하지만 live vehicle detector가 ATS traffic-like target을 최소한 일부는 잡는다는 positive evidence는 생겼다
  - current guard threshold `0.60`을 넘는 confident lead target은 아직 못 봤다
