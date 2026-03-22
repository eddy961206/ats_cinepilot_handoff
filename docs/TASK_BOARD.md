# Task Board

## Done This Session
- [x] `shared_memory_v2` raw capture 도구 추가
- [x] `shared_memory_v2` candidate analysis 도구 추가
- [x] `285:f64`, `293:f64`, `301:f64`를 absolute pose 계약으로 문서화
- [x] decoder가 authoritative absolute pose를 직접 읽도록 정리
- [x] anchored-local frame에서 첫 valid absolute heading 이후에만 anchor heading을 lock하도록 수정
- [x] `absolute_position_hold`로 heading noise를 줄임
- [x] `inspect_telemetry.py`가 pose source / frame / anchor lock / absolute heading 상태를 출력하도록 개선
- [x] 300-step ATS-backed Shadow Mode 재검증 성공

## P0 Next
- [ ] `309:f32`, `325:f32`를 더 체계적으로 비교해서 direct yaw field인지 아닌지 결론 내기
- [ ] 정지, 후진, 저속 회전, 재배치(teleport/recover) 시나리오 capture를 추가로 수집하기
- [ ] 실제 ATS world graph adapter를 연결해서 `anchored_local`이 아닌 global alignment를 검증하기
- [ ] longer live shadow run 5분 이상으로 늘려 freshness / anchor stability / safety 분포 다시 보기

## P1
- [ ] `inspect_telemetry.py --scan-pose-candidates` 결과를 JSON/CSV로 저장하는 모드 추가
- [ ] `json_http` 경로를 계속 유지할지, 보조 경로로만 둘지 결정
- [ ] paused / world-state authoritative field를 추가로 식별하기
- [ ] live replay 샘플 하나를 absolute pose 포함 형식으로 저장하기

## P2
- [ ] HUD preset 1개를 실제 스크린샷으로 캘리브레이션해서 route hint 재연결
- [ ] `scs-sdk-controller` 빌드 툴체인 설치
- [ ] `scscontroller.py` + control plugin 설치 후 dry-run probe 재검증
- [ ] Active Mode 전용 안전 체크리스트 강화
