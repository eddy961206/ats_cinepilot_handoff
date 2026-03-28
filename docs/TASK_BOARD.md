# Task Board

## Done This Session

- [x] durable ops / handoff harness 추가
  - `docs/ops/CURRENT_STATE.md`
  - `docs/ops/ROADMAP.md`
  - `docs/ops/DECISIONS.md`
  - `docs/ops/EXPERIMENT_LOG.md`
  - `docs/ops/FAILED_ATTEMPTS.md`
  - `docs/ops/CHECKLISTS/*`
  - `docs/ops/NEXT_AGENT_BRIEF.md`
  - `state/latest_session_state.json`
  - `scripts/update_session_handoff.py`
- [x] lane observer v1 추가
  - classical ROI/Hough
- [x] vehicle detector v1 추가
  - pretrained OpenCV DNN
  - pinned URL + checksum
- [x] human-visible overlay / CV artifact writer 추가
  - annotated video
  - annotated frames
  - CV summary JSONL
- [x] observer-only dense corridor CV runner 추가
  - `scripts/run_cv_observer_dense_corridor.ps1`
- [x] dense active demo + CV runner 추가
  - `scripts/run_demo_active_dense_corridor_with_cv.ps1`
- [x] first live CV observer overlay run 성공
  - `lane_detected=80/80`
- [x] first dense active demo with CV enabled 성공
  - `NONE=48`
  - `steering_abs_max=0.300`
  - `cv artifacts written`

## P0 Next

- [ ] live traffic가 있는 장면에서 confident lead target evidence 확보
- [ ] lead vehicle guard trigger evidence 1회 확보
- [ ] dense curated corridor demo 반복 재현성 고정
- [ ] curated multi-edge corridor 1개로 확장

## P1

- [ ] barrier / road-edge observer를 narrow한 heuristic으로 추가할지 결정
- [ ] lane guard를 live ATS fixture 기반으로 acceptance test 추가한 뒤 기본 활성화 여부 재판단
- [ ] runtime corridor fit summary를 startup summary / log header에 더 직접 노출
- [ ] module longitudinal(`aforward` / `abackward`) 실패 원인 isolate 계속

## Later

- [ ] curated multi-edge active demo
- [ ] first constrained route-aware demo
- [ ] broader shadow autonomy
- [ ] general Active Mode

## Explicitly Out of Scope Right Now

- [ ] general route-following
- [ ] complex intersections
- [ ] generic CV driving stack
- [ ] wheel actuation
- [ ] dense-local general active driving
- [ ] CV-only control
