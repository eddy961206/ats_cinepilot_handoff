# Task Board

## Done This Session
- [x] 정지 / 좌회전 / 우회전 / 후진 / teleport-recover controlled capture suite 수집
- [x] `309:f32`, `325:f32` heading 후보 비교 결과를 JSON/CSV로 남기도록 분석 툴 확장
- [x] `absolute_discontinuity_distance_m` 기반 discontinuity detection 추가
- [x] teleport/recover jump 시 anchor / heading state reset 추가
- [x] `inspect_telemetry.py`와 recorder에 reset/discontinuity 진단 추가
- [x] 500-step moving live shadow sample로 longer run 한계 재확인

## P0 Next
- [ ] reverse / turn-heavy 시나리오를 더 길게 수집해서 `309:f32`를 direct yaw로 승격할지 최종 결론 내기
- [ ] 500-step moving run 로그를 기준으로 `MATCH_LOST`가 step 267 이후 커지는 원인이 heading인지 toy graph geometry인지 분리하기
- [ ] 실제 ATS world graph adapter를 연결해서 `anchored_local`이 아닌 global alignment를 검증하기
- [ ] longer live shadow run을 여러 driving pattern으로 다시 수집해서 safety 분포를 비교하기

## P1
- [ ] paused / world-state authoritative field를 추가로 식별하기
- [ ] authoritative game tick 후보를 추가로 찾기
- [ ] longer run summary를 자동으로 JSON/CSV로 뽑는 스크립트 추가
- [ ] live replay 샘플 하나를 absolute pose 포함 형식으로 저장하기

## P2
- [ ] HUD preset 1개를 실제 스크린샷으로 캘리브레이션해서 route hint 재연결
- [ ] `scs-sdk-controller` 빌드 툴체인 설치
- [ ] `scscontroller.py` + control plugin 설치 후 dry-run probe 재검증
- [ ] Active Mode 전용 안전 체크리스트 강화
