# CV Observer + Handoff Harness Design

## Goal

기존 dense curated active demo 위에:

1. lane + vehicle CV observer
2. 사람이 바로 볼 수 있는 overlay / artifact
3. future agent가 hidden chat history 없이 이어받을 수 있는 durable handoff harness

를 추가한다.

이번 세션에서 CV는 **primary planner가 아니다**. graph / telemetry / rule-based demo cage가 계속 1차 경로다.

## Current Baseline

- base branch: `main@6eb557371a4806595f4e4fbfa0c28356367bcfd4`
- main에는 curated dense active demo lineage가 이미 들어 있다
- current dense demo:
  - `configs/demo_active_dense_corridor.yaml`
  - `scripts/run_demo_active_dense_corridor.ps1`
- current usable control sink:
  - steering / blinkers -> module
  - throttle / brake -> keyboard

## Approaches Considered

### Approach A: full pretrained lane model + pretrained vehicle model

- 장점:
  - lane semantics가 더 그럴듯할 수 있다
  - overlay 품질이 더 좋을 수 있다
- 단점:
  - lane model asset selection / download / runtime dependency / GPU path 조정이 이번 세션 scope를 쉽게 넘긴다
  - first observer milestone보다 infra 작업이 더 커질 가능성이 높다

### Approach B: classical lane observer + pretrained vehicle detector

- 장점:
  - lane observer는 ATS 화면에 맞춰 빠르게 explainable하게 만들 수 있다
  - vehicle detector는 pretrained DNN을 써서 requirement를 충족한다
  - overlay / artifact / conservative guard까지 이번 세션 안에 닿기 쉽다
- 단점:
  - lane 품질은 pretrained lane model보다 약할 수 있다
  - road edge / barrier는 후순위가 된다

### Approach C: overlay-only observer, no demo integration

- 장점:
  - 가장 안전하고 빠르다
- 단점:
  - user가 요구한 conservative CV guard / assist까지 못 간다

## Selected Approach

**Approach B**를 채택한다.

- lane: lower-road ROI + color/gradient + Hough 기반 lane corridor observer
- vehicles: pretrained OpenCV DNN object detector
- barrier / road edge: 이번 세션에서는 best-effort heuristic만 시도하고, 안 되면 명시적으로 defer
- CV integration: observer / guard / explainability only

## Vehicle Detector Contract

selected pretrained path:

- model family: TensorFlow SSD MobileNet v3 COCO imported through OpenCV DNN
- weights source: OpenCV wiki가 가리키는 TensorFlow official model download
- config source: OpenCV wiki가 가리키는 tested OpenCV config (`pbtxt`)

reason:

- extra Python dependency를 크게 늘리지 않는다
- `opencv-python`만으로 inference path를 유지할 수 있다
- vehicle-like classes (`car`, `bus`, `truck`-adjacent COCO road classes) filtering이 가능하다

## Lane Observer Contract

lane observer v1 output:

- `lane_detected: bool`
- `lane_confidence: float`
- `lane_center_x_px: float | None`
- `lane_offset_px: float | None`
- `lane_width_px: float | None`
- `lane_source: classical_roi_hough`

lane observer v1 algorithm:

1. lower road ROI crop
2. HLS/gray threshold for bright lane paint
3. Canny edge
4. Hough line candidates
5. left/right slope split
6. averaged lane lines -> bottom-center corridor
7. confidence from line count, bilateral presence, corridor stability

## CV Observer Runtime Contract

new config section:

- `cv.enabled`
- `cv.lane.enabled`
- `cv.vehicles.enabled`
- `cv.barrier.enabled`
- `cv.show_window`
- `cv.save_video`
- `cv.save_frames`
- `cv.artifact_dir`
- `cv.vehicle_model.*`
- `cv.guard.*`

observer status fields:

- `cv_enabled`
- `lane_detected`
- `lane_confidence`
- `lane_offset_estimate_px`
- `lead_vehicle_detected`
- `lead_vehicle_confidence`
- `lead_vehicle_box`
- `lead_vehicle_distance_proxy`
- `visual_barrier_risk`
- `cv_guard_reason`

## Overlay Design

observer overlay must show:

- lane left/right lines or corridor polygon
- lane confidence
- lane center offset
- vehicle bounding boxes
- selected lead vehicle
- graph/demo status summary
- current edge id / demo reason if available

two modes:

1. observer-only:
   - real-time window allowed
   - saved annotated video / frames
2. active demo with CV:
   - save artifacts by default
   - overlay window default off to avoid stealing ATS focus

## Safety Integration Design

CV는 demo cage를 replace하지 않는다.

integration policy:

- if lane confidence collapses for configured consecutive frames:
  - disengage with `cv_guard_reason=lane_confidence_low`
- if lead vehicle enters configured center corridor + size/risk threshold:
  - **v1에서는 disengage-only**
  - brake assist는 calibrated threshold evidence가 쌓이기 전까지 기본 비활성
- if barrier risk heuristic fires:
  - disengage only, no attempt to infer steering

guard is behind explicit config flags:

- `cv.guard.enable_lane_guard`
- `cv.guard.enable_lead_vehicle_guard`
- `cv.guard.enable_barrier_guard`

important v1 rule:

- CV는 steering/path planner output을 바꾸지 않는다
- CV가 추가로 할 수 있는 건:
  - annotate
  - status logging
  - disengage
  - optional brake assist flag only if explicitly enabled later

## Lane Guard Validation Rule

lane observer는 synthetic test만으로 guard를 켜지 않는다.

v1 acceptance requirement:

1. synthetic unit test
2. saved ATS frame fixture acceptance
3. live observer artifact spot-check

until then:

- overlay는 켜도 된다
- lane-based hard guard는 default off다

## Vehicle Model Asset Contract

vehicle model asset은 lazy download라도 **fully pinned**여야 한다.

required:

- exact URL
- version identifier
- checksum
- download destination
- offline fallback behavior

if model asset is missing and download is disabled/unavailable:

- observer can still run lane-only mode
- vehicle observer enable은 reject한다
- live demo with vehicle guard는 start하지 않는다

## Handoff Harness Design

required new files:

- `docs/ops/CURRENT_STATE.md`
- `docs/ops/ROADMAP.md`
- `docs/ops/DECISIONS.md`
- `docs/ops/EXPERIMENT_LOG.md`
- `docs/ops/FAILED_ATTEMPTS.md`
- `docs/ops/CHECKLISTS/demo_readiness.md`
- `docs/ops/CHECKLISTS/experiment.md`
- `docs/ops/CHECKLISTS/pr.md`
- `docs/ops/CHECKLISTS/next_session_startup.md`
- `docs/ops/NEXT_AGENT_BRIEF.md`
- `state/latest_session_state.json`
- `scripts/update_session_handoff.py`

rules:

- `CURRENT_STATE.md`와 `EXPERIMENT_LOG.md`는 session 중간에도 계속 갱신
- failed hypothesis는 `FAILED_ATTEMPTS.md`에 남긴다
- next agent는 `NEXT_AGENT_BRIEF.md`와 `CURRENT_STATE.md`를 먼저 읽는다
- helper는 machine-readable facts만 자동 갱신한다
- 수기 판단 / 해석 문단은 helper가 덮어쓰지 않는다

## Deliverables

- `configs/demo_active_dense_corridor_with_cv.yaml`
- `scripts/run_cv_observer_dense_corridor.ps1`
- `scripts/run_demo_active_dense_corridor_with_cv.ps1`
- representative overlay screenshots
- annotated video or frame sequence
- machine-readable perception summaries
- durable handoff docs/state

## Verification Plan

1. current dense demo baseline 재현
2. handoff harness 생성 + state checkpoint
3. observer-only capture run
4. saved overlay artifacts 확인
5. live observer run
6. dense active demo with CV enabled
7. docs/state update 후 PR/merge

## Explicit Non-Goals

- CV-only steering
- graph planner replacement
- generic lane-following autonomy
- route-following autonomy
- complex intersection handling
- training pipeline
