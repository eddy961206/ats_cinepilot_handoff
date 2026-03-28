# Task Board

## Done This Session

- [x] stacked integration lineage를 `main`으로 consolidation
  - PR `#10`
  - merge commit `880cfa5e17da5a9aca8ad304ed350b35dee72021`
- [x] dense curated corridor base contract를 현재 verified freeway chain으로 교체
- [x] corridor-local translated graph helper 추가
  - `scripts/fit_demo_dense_corridor.py`
  - `scripts/export_demo_dense_corridor.py`
- [x] stop preflight 추가
  - `scripts/ensure_demo_stop.py`
- [x] dense demo runner를 runtime fit 기반으로 변경
  - `scripts/run_demo_active_dense_corridor.ps1`
- [x] demo cage start-window priming / bootstrap threshold 보정
- [x] demo override가 `TELEMETRY_STALE` 같은 일반 safety failure를 덮어쓰지 않게 harden
- [x] first curated denser-corridor live active demo 성공
  - `safety NONE = 92`
  - `steering_abs_max = 0.300`
  - `non_trivial_steering_count = 35`

## P0 Next

- [ ] dense curated corridor demo 반복 재현성 고정
- [ ] demo-only longitudinal shaping을 한 단계 더 다듬기
- [ ] curated multi-edge corridor 1개로 확장
- [ ] dense demo helper 결과를 operator-facing artifact로 더 간단히 남기기

## P1

- [ ] runtime corridor fit summary를 startup summary / log header에 더 직접 노출
- [ ] dense corridor 시작 구간 좌표 / edge chain을 runbook에 더 명확히 적기
- [ ] module longitudinal(`aforward` / `abackward`) 실패 원인 isolate 계속
- [ ] dense demo replay artifact를 남겨 bootstrap / armed / brake-assist 구간 비교하기

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
