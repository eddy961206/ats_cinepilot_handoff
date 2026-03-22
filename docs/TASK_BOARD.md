# Task Board

## Done This Session
- [x] `shared_memory_v2` direct reader 구현
- [x] live mapping 이름을 `SCSTelemetrySharedv2_ats`로 확정
- [x] live probe에서 mapping visible + decode 성공 확인
- [x] `inspect_telemetry.py`가 decoded live summary와 stale/layout 실패 분류를 출력하도록 개선
- [x] startup/runtime이 `telemetry.source=shared_memory_v2`를 실제로 실행하도록 연결
- [x] first ATS-backed Shadow Mode run 성공
- [x] `docs/SHARED_MEMORY_V2_DESIGN.md` 추가

## P0 Next
- [ ] absolute world `x/z` offset 후보를 확정해서 relative pose 의존도를 줄이기
- [ ] live shadow를 5분 이상 돌려서 freshness / decode stability / safety reason 분포 확인
- [ ] live shadow 로그를 기준으로 matcher confidence와 route fallback이 실제로 어떤지 정리
- [ ] HUD preset 1개를 실제 스크린샷으로 캘리브레이션해서 route hint를 다시 연결

## P1
- [ ] `inspect_telemetry.py`에 absolute pose 후보 비교 모드 추가
- [ ] `json_http` 경로가 여전히 필요한지 결정
- [ ] `shared_memory_v2` layout이 다른 plugin에서도 같은지 확인
- [ ] `scs-sdk-controller` 빌드 툴체인 설치
- [ ] `scscontroller.py` + control plugin 설치 후 dry-run probe 재검증

## P2
- [ ] active mode 전용 안전 체크리스트 강화
- [ ] 장시간 highway shadow replay 수집
- [ ] better manual override
- [ ] lead vehicle / ACC
- [ ] lane model / segmentation 옵션
