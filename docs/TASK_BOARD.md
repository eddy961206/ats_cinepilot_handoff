# Task Board

## Done This Session
- [x] 실그래프 경로를 `truckermudgeon/maps` 공개 `usa-graph-demo.json` 하나로 고정
- [x] ATS absolute pose <-> WGS84 projection helper 추가
- [x] `trucksim_maps` adapter가 `demoGraph` + `demoNodes`를 직접 로드하도록 확장
- [x] live shared-memory absolute pose를 중심으로 공개 graph를 crop해서 internal cache로 저장하는 export path 추가
- [x] `configs/live_probe_ats_toy_graph.yaml` / `configs/live_probe_ats_real_graph.yaml` 분리
- [x] matcher/app/recorder/startup summary에 graph source / alignment / nearest-edge / candidate diagnostics 추가
- [x] raw shared-memory capture -> replay 변환 도구 추가
- [x] toy graph vs real graph A/B 비교 워크플로 추가
- [x] ATS-backed real-graph shadow sample 1회 추가 검증

## P0 Next
- [ ] 공개 demo graph 대신 polyline/lane 수준 실제 ATS road geometry를 뽑을 concrete exporter/toolchain 하나를 확정
- [ ] 최소 한 지역에 대해 lane-accurate real graph cache를 다시 만들고 현재 `ats_absolute_identity` 정렬을 재검증
- [ ] real graph 기준 route confidence가 왜 0.5 아래에 머무는지 분해
- [ ] turn-heavy longer sample을 lane-accurate graph로 다시 돌려서 `MATCH_LOST`가 graph fidelity 때문인지 최종 확인

## P1
- [ ] direct yaw 후보 `309:f32`를 더 정밀한 real graph와 함께 다시 비교해서 채택 여부 최종 결론 내기
- [ ] paused / world-state authoritative field 식별
- [ ] authoritative game tick 후보 식별
- [ ] A/B 비교 결과를 한 번에 표 형태로 내보내는 summary/report 스크립트 추가

## P2
- [ ] HUD preset 1개를 실제 스크린샷으로 캘리브레이션
- [ ] `scs-sdk-controller` 빌드 툴체인 설치와 control dry-run 재검증
- [ ] control path safety checklist 강화
- [ ] Active Mode 전용 검증 계획 수립
