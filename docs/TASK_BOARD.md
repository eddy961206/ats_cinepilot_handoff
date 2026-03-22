# Task Board

## Done This Session
- [x] `setup_venv.ps1` 실행 확인
- [x] editable install / pytest 실행 확인
- [x] `replay_demo` 단독 실행 경로 복구
- [x] replay shadow mode 상태 로그 추가
- [x] replay recorder에 상태 메타데이터 추가
- [x] `check-config` 검증 강화
- [x] `inspect_telemetry.py` shared-memory / HTTP probe 추가
- [x] `inspect_controls.py` module import / shared-memory / field mapping 점검 추가
- [x] `scscontroller` 기본 필드 매핑 수정
- [x] PR template 추가
- [x] PR workflow 문서화
- [x] live telemetry 경로를 `SCSTelemetrySharedv2`로 명시
- [x] ATS 설치/실행/telemetry plugin load 사실 확인

## P0 Next
- [ ] ATS에서 확장 SDK 기능 확인 팝업을 수동으로 승인해서 `SCSTelemetrySharedv2` 초기화 확인
- [ ] `SCSTelemetrySharedv2` direct reader 구현 여부를 결정하고, 구현이면 최소 필드 읽기까지 연결
- [ ] `scs-sdk-controller` 빌드 툴체인(CMake + MSVC) 설치
- [ ] `scs-sdk-controller` 빌드 후 DLL을 ATS `bin/win_x64/plugins/`에 배치
- [ ] upstream `scscontroller.py`를 Python import 가능 경로에 배치
- [ ] ATS 실행 중 `inspect_controls.py --config configs/default.yaml --dry-run`으로 module import + `Local\SCSControls` 가시성 확인
- [ ] HUD 스크린샷 1장 확보 후 preset 1개 실제 캘리브레이션
- [ ] replay가 아니라 실 telemetry 기반 shadow mode를 1회 성공

## P1
- [ ] `SCSTelemetrySharedv2` shared-memory reader 구현
- [ ] map exporter -> internal graph cache 실제 연결
- [ ] highway shadow mode 5분 로그 수집
- [ ] active mode 전용 dry-run 절차 문서화

## P2
- [ ] highway active mode
- [ ] exit ramp 분기 처리
- [ ] better manual override
- [ ] lead vehicle / ACC
- [ ] lane model / segmentation 옵션
