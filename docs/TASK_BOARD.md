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

## P0 Next
- [ ] ATS용 telemetry plugin 하나 확정하고 실제로 설치
- [ ] ATS 실행 중 `inspect_telemetry.py`로 endpoint 또는 `Local\SCSTelemetry` 가시성 확인
- [ ] `scs-sdk-controller` 빌드 후 DLL을 ATS `bin/win_x64/plugins/`에 배치
- [ ] upstream `scscontroller.py`를 Python import 가능 경로에 배치
- [ ] ATS 실행 중 `inspect_controls.py --config configs/default.yaml --dry-run`으로 module import + `Local\SCSControls` 가시성 확인
- [ ] HUD 스크린샷 1장 확보 후 preset 1개 실제 캘리브레이션
- [ ] replay가 아니라 실 telemetry 기반 shadow mode를 1회 성공

## P1
- [ ] `Local\SCSTelemetry` shared-memory reader 구현 여부 결정
- [ ] map exporter -> internal graph cache 실제 연결
- [ ] highway shadow mode 5분 로그 수집
- [ ] active mode 전용 dry-run 절차 문서화

## P2
- [ ] highway active mode
- [ ] exit ramp 분기 처리
- [ ] better manual override
- [ ] lead vehicle / ACC
- [ ] lane model / segmentation 옵션
