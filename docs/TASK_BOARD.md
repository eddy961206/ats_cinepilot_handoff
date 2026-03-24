# Task Board

## Done This Session

- [x] PR #5가 아직 merge되지 않은 상태임을 확인하고 `codex/real-ats-world-graph-alignment@06d9b67` 위에서 작업 시작
- [x] dense regional graph 설계/spec/plan 추가
- [x] local ATS install + `_ext/trucksim_maps_repo` 기반 dense graph toolchain 하나로 고정
- [x] ATS road GeoJSON adapter 경로 선택
- [x] `scripts/export_local_dense_graph.py` 정리
- [x] `configs/live_probe_ats_dense_local_graph.yaml`를 runtime path로 고정
- [x] dense local geojson cache export 성공
- [x] replay source가 recorder `frame` wrapper를 직접 읽도록 확장
- [x] coarse vs dense local replay A/B 수행
- [x] synthetic reverse edge를 default에서 제거하고 실험용 옵션으로 격리
- [x] 다음 dominant bottleneck을 `route source`가 아니라 `graph-side direction semantics / heading handling`으로 명시

## P0 Next

- [ ] dense local geojson edge direction semantics를 다시 검증
- [ ] raw road feature 방향이 실제 주행 방향과 어긋나는 구간을 분류
- [ ] matcher heading cost와 candidate selection이 straight/light-turn에서 왜 `heading≈π`로 붙는지 분해
- [ ] turn-heavy에서 route confidence는 높은데 `MATCH_LOST`가 나는 이유를 분해
- [ ] 같은 지역에서 direction/heading 수정판으로 A/B 재실행

## P1

- [ ] `309:f32` direct yaw 후보를 dense local geojson graph 위에서 다시 비교
- [ ] paused / world-state authoritative field 식별
- [ ] authoritative game tick 후보 식별
- [ ] replay A/B를 표 형태로 내는 helper script 추가

## Not Yet

- [ ] route source integration
- [ ] control plugin implementation
- [ ] Active Mode
