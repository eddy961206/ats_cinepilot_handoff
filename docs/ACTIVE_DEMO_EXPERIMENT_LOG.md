# Active Demo Experiment Log

## 2026-03-26

### Base

- base branch: `codex/real-ats-world-graph-alignment@3443e94707d7f17c32cee488753627251393eab4`
- working branch: `codex/gentle-curve-active-demo`

### Goal

- 직선 constrained active demo를 유지하면서, 첫 visible closed-loop steering이 있는 gentle-curve active demo를 만든다.

### Baseline Reproduction

- straight demo helper 재실행:
  - `powershell -ExecutionPolicy Bypass -File scripts\run_demo_active_corridor.ps1 -ShadowSteps 20 -ActiveSteps 80 -ActiveCountdownSeconds 8`
- 결과:
  - readiness 통과
  - `step 39`에서 `demo=armed/armed`
  - `step 52`에서 `speed=4.07 m/s`, `DEMO_GUARD`, `speed_cap_exceeded`
  - steering은 거의 0에 가까움
- straight summary:
  - `steering_abs_max=0.065`
  - `non_trivial_steering_count=6`
  - `throttle_command_count=1479`
  - `brake_command_count=93`

### Curved Corridor Setup

- added:
  - `data/maps/cache/demo_gentle_curve_graph.json`
  - `configs/demo_active_gentle_curve.yaml`
  - `scripts/run_demo_active_gentle_curve.ps1`
- selected corridor contract:
  - `graph_source=toy_gentle_curve_graph`
  - `alignment_mode=anchored_local_toy_graph`
  - `approved_edge_ids=["curve_ab"]`
  - `max_speed_mps=3.0`
  - `max_progress_m=38.0`
  - corridor label is intentionally direction-neutral in runtime config because operator visual direction naming is not yet a trustworthy contract

### Curved Shadow Qualification

- command:
  - `powershell -ExecutionPolicy Bypass -File scripts\run_demo_active_gentle_curve.ps1 -ShadowSteps 25 -ActiveSteps 0 -ActiveCountdownSeconds 0 -ShadowOnly`
- result:
  - `safety={NONE: 25}`
  - `steering_abs_max=0.000`
  - `non_trivial_steering_count=0`
  - car was stationary, so this only verified cage/readiness, not curve steering demand

### Curved Active Attempt #1

- command:
  - `powershell -ExecutionPolicy Bypass -File scripts\run_demo_active_gentle_curve.ps1 -ShadowSteps 25 -ActiveSteps 120 -ActiveCountdownSeconds 8`
- summary:
  - `steps=145`
  - `safety={NONE: 50, DEMO_GUARD: 24, MATCH_LOST: 71}`
  - `first_MATCH_LOST=43`
  - `match=[0.969, 1.000]`
  - `route=[0.646, 0.700]`
  - `cte_max=1.390`
  - `steering_abs_max=0.400`
  - `non_trivial_steering_count=89`
  - `throttle_command_count=127`
  - `brake_command_count=15`
  - `demo_guard_reasons={bootstrap: 41, heading_source_unapproved: 3, arming: 11, armed: 9, speed_cap_exceeded: 17, cross_track_error_high: 28, match_confidence_low: 36}`

### Interpretation

- confirmed:
  - gentle-curve attempt produced real non-zero closed-loop steering commands
  - throttle/brake remained active in the same run
- failed:
  - corridor did not stay inside the demo cage long enough
  - `cross_track_error_high` and later `match_confidence_low` dominated

### New Hypotheses

1. steering sign may be inverted relative to the planner/controller convention
2. steering magnitude may be too aggressive for the current toy curve shape
3. toy curve geometry may not match the actual ATS road segment closely enough

### Safety Note

- one manual `steering=+1.0, hold=3s` pulse was too large for safe diagnosis
- future steering sign probes must stay at or below `0.20 ~ 0.25` with short hold time

### Additional Live Evidence

- user observation:
  - one `steering=+1.0, hold=3s` module pulse appeared to spin the wheel far past a reasonable demo diagnostic range
  - user could not confidently label the visual direction in left/right terms
- consequence:
  - future sign probes must use relative comparison against a known keyboard input (`A` or `D`) rather than asking for absolute direction naming

### Curved Active Attempt #1 Tail Diagnosis

- tail sample from `data/logs/demo_active_gentle_curve.jsonl` showed:
  - `command.steering=+0.400` held at saturation
  - `graph_candidate_count=1`
  - `selected_edge_id=curve_ab`
  - `selected_travel_direction=forward`
  - `direction_classification=aligned`
  - `cross_track_error_m` rising from `1.06` to `1.39`
  - `heading_error_rad` remaining negative (`~-0.23` then `~-0.33`)
  - `match_confidence` decaying from `0.9798` to `0.9688`
  - `route_confidence` decaying from `0.6621` to `0.6461`
- interpretation:
  - the matcher did not flip candidates or lose graph continuity first
  - the controller kept commanding the same signed steering while the truck continued drifting away from the approved curve
  - this makes steering-sign mismatch or curve-shape mismatch more likely than a candidate-selection failure

### Raw Steering-Sign Probe

- one raw shared-memory experiment sampled baseline / `+0.20` steering pulse / `-0.20` steering pulse while stationary
- result:
  - decoded yaw remained effectively unchanged because the truck was not moving
  - naive raw `f32` offset scan produced too many unstable candidates to identify a trustworthy steering semantic
- conclusion:
  - stationary shared-memory scanning is not sufficient to infer steering sign
  - next safe probe should compare module steering pulse direction to a known manual `A` key steering action

### Root-Cause Narrowing After Candidate Review

- code inspection confirmed there is no additional steering sign inversion layer between pure pursuit output and the module sink write path
- live curved run evidence showed the first meaningful control window behaved plausibly:
  - non-zero steering stayed in the `+0.16 ~ +0.20` range while yaw initially changed smoothly along the approved gentle curve
  - the first hard disengage happened at `speed=3.10 m/s` because `demo.max_speed_mps=3.0`
- after that first guard event, live steering authority was removed and the truck drifted outward while the logged planner demand later saturated at `+0.4`
- current root-cause ranking:
  1. coarse digital longitudinal actuation (`W/S`) is too blunt for the gentle low-speed curve cage
  2. toy curve geometry mismatch remains possible
  3. steering sign inversion is currently lower-confidence than the two causes above

### Follow-Up Change In Progress

- added a demo-usable keyboard longitudinal PWM path to reduce binary `W/S` aggressiveness at low speed
- selected initial setting for the curved demo profile:
  - `control.keyboard.longitudinal_pwm_period_s=0.25`
- next live validation goal:
  - check whether the curved demo stays armed longer before any `speed_cap_exceeded`
  - then re-evaluate whether remaining drift is primarily geometry mismatch

### Curved Active Attempt #2 After Longitudinal PWM

- config change:
  - `control.keyboard.longitudinal_pwm_period_s=0.25`
- command:
  - `powershell -ExecutionPolicy Bypass -File scripts\run_demo_active_gentle_curve.ps1 -ShadowSteps 25 -ActiveSteps 120 -ActiveCountdownSeconds 8`
- summary:
  - `steps=145`
  - `safety={NONE: 111, MATCH_LOST: 9, DEMO_GUARD: 24, ROUTE_CONFIDENCE_LOW: 1}`
  - `first_MATCH_LOST=92`
  - `match=[0.997, 1.000]`
  - `route=[0.681, 0.700]`
  - `cte_max=0.240`
  - `steering_abs_max=0.209`
  - `non_trivial_steering_count=32`
  - `throttle_command_count=126`
  - `brake_command_count=18`
  - `demo_guard_reasons={bootstrap: 91, heading_source_unapproved: 4, arming: 11, armed: 20, speed_cap_exceeded: 19}`
- interpretation:
  - PWM reduced the earlier blow-up materially
  - the run stayed inside `safety=NONE` much longer than attempt #1
  - visible closed-loop steering became demo-worthy, but speed-cap guard still triggered before a very long stable run

### Curved Active Attempt #3 Repeatability Check

- command:
  - `powershell -ExecutionPolicy Bypass -File scripts\run_demo_active_gentle_curve.ps1 -ShadowSteps 25 -ActiveSteps 120 -ActiveCountdownSeconds 10`
- summary:
  - `steps=145`
  - `safety={NONE: 130, MATCH_LOST: 4, DEMO_GUARD: 11}`
  - `first_MATCH_LOST=120`
  - `match=[1.000, 1.000]`
  - `route=[0.694, 0.700]`
  - `cte_max=0.235`
  - `steering_abs_max=0.211`
  - `non_trivial_steering_count=22`
  - `throttle_command_count=145`
  - `brake_command_count=0`
  - `demo_guard_reasons={bootstrap: 119, heading_source_unapproved: 4, arming: 11, armed: 11}`
- operator observation:
  - user reported visible steering toward the right during the repeatability run
- updated interpretation:
  - the runtime corridor should stay direction-neutral in labels and docs until left/right semantics are explicitly calibrated
  - this run is still a valid demo success because the tracked edge stayed singular and the safety envelope held far longer
  - no steering-sign flip should be merged from this observation alone
