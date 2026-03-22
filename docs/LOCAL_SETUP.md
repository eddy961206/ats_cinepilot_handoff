# Local Setup (Windows 11)

## 1. 가상환경

```powershell
.\scripts\setup_venv.ps1
```

이번 세션에서 실제로 성공했다.

## 2. 현재 선택된 live telemetry 경로

이 저장소가 지금 우선 지원하는 경로는 **MOZA shared memory v2**다.

- plugin DLL: `atssharedplugin64v2.dll`
- mapping name: `SCSTelemetrySharedv2_ats`
- probe config: `configs/live_probe_moza_shared_memory.yaml`
- 설계 메모: `docs/SHARED_MEMORY_V2_DESIGN.md`

RenCloud `Local\SCSTelemetry` 경로는 여전히 참고용이지만, 이 머신에서 첫 live validation을 통과한 경로는 아니다.

## 3. 외부 구성요소

### telemetry
- ATS plugin DLL은 `bin\win_x64\plugins\` 아래에 있어야 한다.
- 이 머신에서는 아래 경로가 실제로 확인됐다.

```text
D:\Steam\steamapps\common\American Truck Simulator\bin\win_x64\plugins\atssharedplugin64v2.dll
```

### controls
- control path는 아직 다음 단계다.
- 나중에 `scs-sdk-controller`를 쓸 경우:
  - DLL을 ATS `bin\win_x64\plugins\` 아래에 둬야 함
  - Python 쪽 `scscontroller.py`도 import 가능해야 함

## 4. 설정 검증

replay:

```powershell
.\.venv\Scripts\ats-cinepilot check-config --config configs\profiles\replay_demo.yaml
```

live shared memory:

```powershell
.\.venv\Scripts\ats-cinepilot check-config --config configs\live_probe_moza_shared_memory.yaml
```

## 5. telemetry probe

```powershell
.\.venv\Scripts\python scripts\inspect_telemetry.py --config configs\live_probe_moza_shared_memory.yaml --frames 5
```

이 스크립트는 이제 아래를 보여준다.

- ATS 실행 여부
- plugin DLL 경로
- mapping visibility
- decode 성공 여부
- sampled frame별 update token / speed / rpm / gear / throttle / pose
- stale/layout failure 분류

이번 세션의 실제 결과:

- ATS 실행 중
- `SCSTelemetrySharedv2_ats` visible
- decode 성공
- live update token 변화 확인
- `telemetry status: telemetry ready`

## 6. replay smoke

```powershell
.\.venv\Scripts\ats-cinepilot run --config configs\profiles\replay_demo.yaml --mode shadow --steps 5
```

이번 세션에서 실제로 성공했다.

## 7. live shadow smoke

```powershell
.\.venv\Scripts\ats-cinepilot run --config configs\live_probe_moza_shared_memory.yaml --mode shadow --steps 30
```

이번 세션의 실제 결과:

- startup summary 출력 확인
- live telemetry ingest 성공
- step log 출력 확인
- recorder 파일 생성 확인: `data/logs/live_probe_moza_shadow.jsonl`

중요:
- 지금 reader의 pose는 absolute world pose가 아니라 relative pose다.
- 그래서 이 성공은 **live telemetry 경로 bring-up 성공**이지, full route-following 품질 검증 완료를 뜻하지는 않는다.

## 8. controls probe

```powershell
.\.venv\Scripts\python scripts\inspect_controls.py --config configs\default.yaml --dry-run
```

이번 세션 기준으로는 아직 아래 상태다.

- `scscontroller` module 없음
- control plugin DLL 없음
- Active Mode 검증 금지
