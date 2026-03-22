# Local Setup (Windows 11)

## 1. 가상환경

```powershell
.\scripts\setup_venv.ps1
```

이번 세션에서 위 스크립트는 실제로 성공했다.

## 2. 외부 구성요소

아래 중 최소 하나씩 준비해야 한다.

### 텔레메트리
권장 경로 A:
- SCS Telemetry SDK 기반 shared-memory plugin
- 예: RenCloud `scs-sdk-plugin`
- 기대 shared memory 이름: `Local\SCSTelemetry`

현재 이 머신에서 실제로 잡힌 경로:
- plugin DLL: `D:\Steam\steamapps\common\American Truck Simulator\bin\win_x64\plugins\atssharedplugin64v2.dll`
- shared memory 이름: `SCSTelemetrySharedv2`
- 추천 live probe config: `configs/live_probe_moza_shared_memory.yaml`

권장 경로 B:
- JSON wrapper 서비스
- 기본 config는 `http://127.0.0.1:25555/api/telemetry`를 가정함
- 실제 field map은 아직 실환경 미검증

### 게임 제어
권장:
- `scs-sdk-controller` 기반 제어 경로
- 기대 shared memory 이름: `Local\SCSControls`
- upstream Python client의 주요 필드명:
  - `steering`
  - `aforward`
  - `abackward`
  - `lblinker`
  - `rblinker`

fallback:
- keyboard/mouse 방식
- vJoy 같은 가상 장치

하지만 v1 목표는 게임 내부/SDK 계열 입력 경로 우선이다.

### 맵 export
- `truckermudgeon/maps`
- 또는 `ts-map`

## 3. 외부 플러그인 배치

### telemetry plugin
- shared-memory plugin을 쓰면 ATS 설치 경로의 `bin\win_x64\plugins\` 아래에 DLL을 둬야 한다.
- JSON wrapper를 쓰면 별도 서비스가 로컬에서 떠 있어야 한다.

### control plugin
- `scs-sdk-controller`는 upstream README 기준 CMake로 빌드해야 한다.
- 빌드된 DLL도 ATS `bin\win_x64\plugins\` 아래에 둬야 한다.
- Python 쪽에서는 upstream `scscontroller.py`가 import 가능해야 한다.
- 가장 단순한 방법은 이 저장소의 `src\scscontroller.py` 위치에 upstream 파일을 두는 것이다.

## 4. 설정 검증

replay만 먼저 확인할 때:

```powershell
.\.venv\Scripts\ats-cinepilot check-config --config configs\profiles\replay_demo.yaml
```

실 ATS용 기본 설정을 볼 때:

```powershell
.\.venv\Scripts\ats-cinepilot check-config --config configs\default.yaml
```

선택한 live telemetry probe 설정:

```powershell
.\.venv\Scripts\ats-cinepilot check-config --config configs\live_probe_moza_shared_memory.yaml
```

## 5. smoke test

### telemetry

```powershell
python scripts\inspect_telemetry.py --config configs\live_probe_moza_shared_memory.yaml
```

이 스크립트는 이제 아래를 같이 보여준다.
- ATS 실행 여부
- selected shared memory 이름
- plugin DLL 존재 여부
- game.log 기준 plugin load 여부
- shared memory initialized 여부 추정
- 실패 분류 결과

이번 세션의 실제 결과:
- ATS 실행 중
- `atssharedplugin64v2.dll` 존재
- `game.log`에서 plugin load 확인
- `SCSTelemetrySharedv2`는 아직 안 열림
- 원인 추정: 메인 메뉴/SDK 확인 팝업 gate

### controls

```powershell
python scripts\inspect_controls.py --config configs\default.yaml --dry-run
```

이 스크립트는 이제 아래를 같이 보여준다.
- `scscontroller` import 가능 여부
- `scs_sdk_controller.dll` 존재 여부
- `Local\SCSControls` 가시성
- field mapping이 upstream client와 맞는지
- 실패 분류 결과

주의:
- `scscontroller` 클라이언트는 스스로 shared memory를 만들 수 있다.
- 그래서 "attach/apply 성공"만으로 ATS plugin이 실제로 듣고 있다고 단정하면 안 된다.
- 반드시 **attach 전 probe 결과**도 같이 봐야 한다.

이번 세션의 실제 결과:
- `scscontroller` module 없음
- `scs_sdk_controller.dll` 없음
- 이 머신에는 아직 CMake / `cl`도 없음

## 6. HUD 캘리브레이션

게임 스크린샷을 하나 저장한 뒤:

```powershell
python scripts\calibrate_hud.py --config configs\default.yaml --image C:\path\to\ats_route_widget.png
```

출력 이미지가 `data/calibrations/` 아래 생긴다.

## 7. replay / shadow

```powershell
ats-cinepilot run --config configs\profiles\replay_demo.yaml --mode shadow --steps 500
```

이번 세션에서 위 커맨드는 실제로 성공했다.

## 7.5 live probe / blocker 확인

```powershell
.\.venv\Scripts\python scripts\inspect_telemetry.py --config configs\live_probe_moza_shared_memory.yaml --frames 1
```

현재 이 커맨드는 아래 blocker를 보여준다.
- ATS는 실행 중
- plugin DLL도 있음
- 하지만 `SCSTelemetrySharedv2`가 아직 초기화되지 않음
- 따라서 첫 live shadow run 전 단계에서 멈춰 있음

## 8. active mode 전 체크리스트

- telemetry 안정적으로 읽힘
- `inspect_controls.py --dry-run`에서 module import + field mapping 확인
- `Local\SCSControls`가 ATS 실행 중 visible
- map match 튀지 않음
- HUD route mask가 빨간 길만 잡음
- safety 임계값이 너무 느슨하지 않음
