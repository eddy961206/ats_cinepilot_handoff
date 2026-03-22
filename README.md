# ATS CinePilot

ATS에서 **내비게이션을 따라 안정적으로 주행**하는 “경치 구경용” 자율주행 프로젝트 스캐폴드야.

이 저장소는 바로 완성된 상용급 자율주행 구현체가 아니라, 네 로컬 PC에서 돌아가는 **codex 실행 에이전트**가 이어받아서 설치/실행/디버깅/수정/반복할 수 있게 만든 **핸드오프 패키지**다.

핵심 방향은 이거야.

- 순수 화면 AI보다 **텔레메트리 + 도로 그래프 + HUD 경로 힌트 + 규칙 기반 제어기** 구조를 우선한다.
- 첫 목표는 “도시/복잡 교차로 완전정복”이 아니라 **고속도로 위주 안정 주행 + 안전한 해제**다.
- 딥러닝 차선 모델은 v2 이후 옵션이다.
- MOZA R3는 v1에선 **수동 takeover 장치**로 취급한다.
- 네 로컬 codex가 바로 이어서 작업할 수 있게 문서와 TODO를 자세히 넣어놨다.

## 지금 들어있는 것

- Python 프로젝트 스캐폴드
- 아키텍처 문서
- codex용 핸드오프 문서
- config 시스템
- 텔레메트리/입력/캡처 브리지의 인터페이스와 일부 구현
- HUD route mask / turn bias 추출용 CV 파이프라인 초안
- 도로 그래프 / pose matching / preview path / speed profile / pure pursuit / PID 틀
- safety arbiter 틀
- replay / logging / overlay / 테스트 골격
- Windows PowerShell helper 스크립트

## 일부러 비워둔 것

여기는 네 로컬 codex가 실제 PC 환경에서 검증하면서 채워야 한다.

- 실제 SCS shared-memory 구조의 완전 검증
- `scs-sdk-controller`와의 정확한 필드 매핑
- HUD 위젯 실제 위치/배율/FOV 캘리브레이션
- 맵 exporter 출력 스키마에 맞춘 adapter 마무리
- ATS 실제 주행 데이터 기반 튜닝
- active mode 실차(?) 아니고 실제 게임 주행 검증

## 폴더 구조

```text
ats_cinepilot_handoff/
├─ configs/
├─ data/
├─ docs/
├─ scripts/
├─ src/ats_cinepilot/
└─ tests/
```

## 추천 작업 순서

1. `docs/CODEX_HANDOFF.md` 먼저 읽기
2. `.\scripts\setup_venv.ps1`
3. `ats-cinepilot check-config --config configs/profiles/replay_demo.yaml`
4. `ats-cinepilot run --config configs/profiles/replay_demo.yaml --mode shadow --steps 300`
5. `ats-cinepilot check-config --config configs/live_probe_moza_shared_memory.yaml`
6. `python scripts/inspect_telemetry.py --config configs/live_probe_moza_shared_memory.yaml`
7. `python scripts/inspect_controls.py --config configs/default.yaml --dry-run`
8. `python scripts/calibrate_hud.py ...` 로 HUD 마스크 캘리브레이션
9. 실 telemetry shadow mode
10. shadow mode가 안정되면 active mode로 확대

## 빠른 시작 예시

```powershell
.\scripts\setup_venv.ps1
.\.venv\Scripts\ats-cinepilot check-config --config configs\profiles\replay_demo.yaml
.\.venv\Scripts\ats-cinepilot run --config configs\profiles\replay_demo.yaml --mode shadow --steps 300
```

실 ATS 연결 전 확인:

```powershell
.\.venv\Scripts\python scripts\inspect_telemetry.py --config configs\live_probe_moza_shared_memory.yaml
.\.venv\Scripts\python scripts\inspect_controls.py --config configs\default.yaml --dry-run
```

## 외부 의존성

이 저장소 안에는 외부 프로젝트의 바이너리나 코드를 번들하지 않았다.

필요할 가능성이 높은 외부 요소는 문서에 정리해뒀다.

- SCS Telemetry SDK / 텔레메트리 플러그인
- `scs-sdk-controller`
- `truckermudgeon/maps` 또는 `ts-map`
- DXcam

자세한 건 `docs/PLUGIN_OPTIONS.md` 참고.

## 중요한 현실 체크

이번 세션 기준으로는 아래까지 실제 확인됐다.
- replay profile 단독 실행
- editable install
- pytest 전체 통과
- replay shadow 상태 로그 출력

아직 확인 안 된 건 아래다.
- ATS 1.58 실 telemetry 입력
- `scs-sdk-controller` 기반 실제 control write
- HUD 실제 캘리브레이션
- active mode

지금 선택된 live telemetry 경로는 `SCSTelemetrySharedv2` shared memory고, 이건 `configs/live_probe_moza_shared_memory.yaml`에 반영돼 있어.

이번 세션에서 실제로 확인한 blocker는 이거야.
- ATS는 설치돼 있고 실행도 됐음
- `atssharedplugin64v2.dll`도 로드됐음
- 하지만 메인 메뉴의 SDK 확인 팝업 gate 때문에 `SCSTelemetrySharedv2`가 아직 열리지 않았음
- direct reader도 아직 구현 안 됐음

그 대신, codex가 헤매지 않도록:
- 모듈 경계를 강하게 나눴고
- 우선순위를 문서로 못 박았고
- shadow mode 중심으로 점진적 검증 흐름을 넣었고
- 어디가 추정이고 어디가 미검증인지 솔직하게 적어뒀다.

## 문서 맵

- `docs/CODEX_HANDOFF.md`  
  네 codex가 제일 먼저 읽어야 하는 문서
- `docs/ARCHITECTURE.md`  
  전체 구조 설명
- `docs/IMPLEMENTATION_STATUS.md`  
  지금 구현된 것 / 아직 비어있는 것
- `docs/LOCAL_SETUP.md`  
  Windows 11 기준 로컬 설치 절차
- `docs/PLUGIN_OPTIONS.md`  
  외부 플러그인/도구 추천
- `docs/RESEARCH_NOTES.md`  
  조사 메모와 참고 링크
- `docs/RUNBOOK.md`  
  반복 실험 루프
- `docs/SAFETY.md`  
  자동주행 해제 기준
