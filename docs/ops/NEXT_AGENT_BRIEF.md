# Next Agent Brief

- manual summary:
  - dense demo baseline is alive but still placement-sensitive
  - CV observer + overlay + ops handoff harness now exist
  - do not turn CV into primary steering/planning
- next concrete work:
  - capture a live traffic scene with a confident lead target
  - verify lead-vehicle guard on a real positive case
  - then expand to curated multi-edge dense corridor
- do not repeat blindly:
  - assume observer-only checked-in dense graph run says anything about runtime-fit dense demo quality

<!-- BEGIN AUTO-GENERATED FACTS -->
- auto base: `main@6eb557371a4806595f4e4fbfa0c28356367bcfd4`
- auto branch: `codex/cv-observer-handoff-harness`
- auto stage: `C3.5`
- auto focus: `cv_observer_overlay_guard_verified`
- auto head commit: `89189c935a274bb3d0f989fe0de58b92659ef507`
- auto last known good commands:
  - `powershell -ExecutionPolicy Bypass -File scripts\run_cv_observer_dense_corridor.ps1 -Steps 80`
  - `powershell -ExecutionPolicy Bypass -File scripts\run_demo_active_dense_corridor_with_cv.ps1 -ShadowSteps 8 -ActiveSteps 80 -ActiveCountdownSeconds 3`
  - `powershell -ExecutionPolicy Bypass -File scripts\run_demo_active_dense_corridor_with_cv.ps1 -ShadowSteps 4 -ActiveSteps 40 -ActiveCountdownSeconds 3`
- auto latest artifacts:
  - `data\artifacts\cv\observer_dense_corridor\observer_overlay.mp4`
  - `data\artifacts\cv\demo_active_dense_corridor\observer_overlay.mp4`
  - `data\logs\cv_observer_dense_corridor.cv.jsonl`
  - `data\logs\demo_active_dense_corridor_with_cv.cv.jsonl`
- auto blockers:
  - `module_longitudinal_unusable`
  - `dense_demo_repeatability_unstable`
  - `lead_vehicle_guard_trigger_missing`
  - `barrier_observer_deferred`
<!-- END AUTO-GENERATED FACTS -->
