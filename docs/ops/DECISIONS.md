# Decisions

## 2026-03-29 — Keep CV as observer/guard, not primary planner

- decision:
  - CV는 lane / vehicle observer와 safety/overlay layer로만 넣는다
- reason:
  - current project philosophy is telemetry + graph first
  - this session 목표는 general autopilot이 아니라 observability + conservative guard다
- evidence:
  - dense curated active demo baseline already exists without CV
- tradeoff:
  - CV가 steering planner 역할을 못 하니 기능 확장은 제한적이다
  - 대신 scope가 reviewable하고 안전하다

## 2026-03-29 — Lane observer v1 uses classical ROI/Hough pipeline

- decision:
  - lane observer는 first pass에서 classical pipeline으로 간다
- reason:
  - pretrained lane model 도입은 asset/runtime complexity가 크다
  - 이번 세션 핵심은 visible overlay와 conservative signals다
- evidence:
  - OpenCV + ATS capture path is already present
- tradeoff:
  - lane quality는 limited할 수 있다
  - barrier/road-edge는 후순위가 된다

## 2026-03-29 — Vehicle observer uses pretrained OpenCV DNN detector

- decision:
  - road vehicle detection은 pretrained OpenCV DNN detector를 쓴다
- reason:
  - off-the-shelf pretrained requirement를 만족한다
  - extra runtime dependency를 크게 늘리지 않는다
- evidence:
  - OpenCV wiki tested TensorFlow object detection path exists
- tradeoff:
  - ATS-specific class quality는 완벽하지 않을 수 있다

## 2026-03-29 — Lead vehicle CV guard stays disengage-only in v1

- decision:
  - lead vehicle guard는 v1에서 disengage-only로 제한한다
- reason:
  - 2D bounding box만으로 brake assist 거리 추정까지 믿기엔 아직 근거가 약하다
- evidence:
  - live observer run에서는 vehicle target이 아예 잡히지 않은 구간도 있었다
  - current dense demo primary safety cage already exists
- tradeoff:
  - CV가 적극적인 longitudinal intervention을 아직 못 한다
  - 대신 false positive brake risk를 줄인다

## 2026-03-29 — Session handoff helper updates only managed facts

- decision:
  - `scripts/update_session_handoff.py`는 `NEXT_AGENT_BRIEF.md` 전체를 덮어쓰지 않고 managed section만 갱신한다
- reason:
  - future agents가 manual summary를 잃지 않아야 한다
- evidence:
  - long sessions / context compression에서는 짧은 manual brief가 중요하다
- tradeoff:
  - fully automatic doc regeneration 범위는 줄어든다
  - 대신 사람이 적은 brief와 auto facts가 안정적으로 공존한다

## 2026-03-29 — CV model assets are pinned by URL plus checksum, but not checked in

- decision:
  - vehicle model assets는 체크섬으로 고정하고 helper script로 받되, repo에는 binary를 넣지 않는다
- reason:
  - repo 무게를 늘리지 않으면서도 reproducibility를 유지하려는 선택이다
- evidence:
  - `scripts/download_cv_models.py`
  - `cv.vehicles.model_url / pbtxt_url / sha256`
- tradeoff:
  - first run에 download step이 필요하다
  - upstream mirror availability가 또 깨지면 URL pin 교체가 필요할 수 있다
