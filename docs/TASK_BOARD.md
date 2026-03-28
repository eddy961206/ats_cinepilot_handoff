# Task Board

## Done This Session

- [x] correct integration base 확인
  - `main`이 아니라 `codex/real-ats-world-graph-alignment@3443e947...` 기반
- [x] straight active baseline 재현
- [x] gentle-curve toy corridor 자산 추가
  - `data/maps/cache/demo_gentle_curve_graph.json`
  - `configs/demo_active_gentle_curve.yaml`
  - `scripts/run_demo_active_gentle_curve.ps1`
- [x] curved demo startup summary / log summary 보강
- [x] curved demo 실험 노트 파일 추가
  - `docs/ACTIVE_DEMO_EXPERIMENT_LOG.md`
- [x] root-cause narrowing
  - steering sign은 1순위 병목이 아님
  - speed cap / digital longitudinal bluntness가 먼저 걸림
- [x] demo-only keyboard longitudinal PWM 경로 추가
- [x] first gentle-curve constrained live active demo 성공
  - `steering_abs_max=0.209`
  - `non_trivial_steering_count=32`
  - `first_MATCH_LOST=92`

## P0 Next

- [ ] `run_demo_active_gentle_curve.ps1`를 human-run 기준으로 반복 재현
- [ ] curved demo에서 speed cap guard를 덜 거칠게 만들도록 demo-only longitudinal shaping을 한 단계 더 다듬기
- [ ] curated denser corridor 1개로 확장 가능한지 판단
- [ ] module longitudinal(`aforward` / `abackward`) 실패 원인 isolate 계속

## P1

- [ ] hybrid sink focus preflight를 더 강하게 안내하거나 probe로 노출할지 결정
- [ ] gentle-curve run의 replay-style artifact를 남겨 arming / disengage 비교하기
- [ ] curve demo throttle shaping taxonomy 문서화
  - keyboard focus dependency
  - duty-cycle granularity
  - speed cap overshoot
  - corridor geometry mismatch

## Later

- [ ] curated denser active corridor
- [ ] constrained route source
- [ ] broader shadow autonomy
- [ ] Active Mode 일반화

## Explicitly Out of Scope Right Now

- [ ] generic CV driving stack
- [ ] wheel actuation
- [ ] broad route-following autonomy
- [ ] complex intersection handling
- [ ] dense-local general active driving
