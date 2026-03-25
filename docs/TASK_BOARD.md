# Task Board

## Done This Session

- [x] base branch lineage 확인
  - `main`이 아니라 PR #6/#7 stacked lineage 위에서 작업
- [x] control path를 실제로 다시 검증
  - module steering visual OK
  - module blinker visual OK
  - module longitudinal 실패를 telemetry로 확인
  - keyboard longitudinal 성공 확인
- [x] `hybrid` sink 추가
  - steering / blinkers -> module
  - throttle / brake -> keyboard
- [x] demo startup / config / control probe를 `hybrid` 기준으로 갱신
- [x] demo brake assist + PID integral limit 보강
- [x] constrained live hybrid micro-probe 성공
- [x] first constrained live active demo attempt 성공
- [x] operator helper / docs를 active demo 기준으로 갱신

## P0 Next

- [ ] `run_demo_active_corridor.ps1`를 human-run 기준으로 한 번 더 반복 재현
- [ ] ATS focus requirement를 더 강하게 운영 절차에 고정
- [ ] module longitudinal(`aforward` / `abackward`)이 왜 안 먹는지 별도 isolate
- [ ] toy corridor를 벗어나기 전에 “approved corridor 2개째”를 만들 수 있는지 판단

## P1

- [ ] `hybrid` sink를 위한 foreground/focus preflight probe 추가 여부 검토
- [ ] constrained corridor replay artifact를 남겨 active arming/disengage를 더 비교하기
- [ ] module longitudinal failure taxonomy 문서화
  - binding mismatch
  - semantic input behavior
  - ATS state dependency
  - plugin-side issue

## Later

- [ ] dense local graph corridor 확장
- [ ] constrained route source
- [ ] broader shadow autonomy
- [ ] Active Mode 일반화

## Explicitly Out of Scope Right Now

- [ ] generic CV driving stack
- [ ] wheel actuation
- [ ] broad route-following autonomy
- [ ] complex intersection handling
