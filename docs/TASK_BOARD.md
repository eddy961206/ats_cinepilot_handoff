# Task Board

## Done This Session

- [x] PR #5는 `main`에 merge됐고 PR #6는 `codex/real-ats-world-graph-alignment`에만 merge된 상태임을 확인
- [x] 이번 브랜치를 `origin/codex/real-ats-world-graph-alignment@04bf533` 위에서 시작
- [x] dense forward-only baseline을 replay로 다시 재현
- [x] matcher candidate direction diagnostics 추가
- [x] recorder / shadow summary에 `selected_reason`, `direction_confidence_state`, top candidate snapshot 연결
- [x] scoped reverse-heading rescue 추가
- [x] continuity bonus distance gating 추가
- [x] matcher tuning 값을 config(`map.*`)로 노출
- [x] coarse vs dense fresh post-change replay A/B 수행
- [x] live shared_memory_v2 probe 재실행
- [x] 이번 세션 dominant bottleneck을 `route source`가 아니라 `dense local graph geometry / candidate topology fidelity`로 명시

## P0 Next

- [ ] turn-heavy에서 cte가 커지는 edge ID 구간을 추출하고 실제 GeoJSON geometry와 대조
- [ ] dense local crop radius / region 선택이 problematic segment를 잘 포함하는지 검증
- [ ] candidate topology가 잘못된 구간인지, edge geometry가 어긋난 구간인지 분류
- [ ] 필요하면 dense local export를 더 좁고 더 정확한 corridor 기준으로 다시 생성
- [ ] 그 다음에만 matcher continuity/heading cost를 한 번 더 조정

## P1

- [ ] `309:f32` direct yaw 후보를 dense local graph geometry 점검 이후 다시 비교
- [ ] paused / world-state authoritative field 식별
- [ ] authoritative game tick 후보 식별
- [ ] replay A/B + direction diagnostics를 표/CSV로 내는 helper script 추가

## Not Yet

- [ ] route source integration
- [ ] control plugin implementation
- [ ] Active Mode
