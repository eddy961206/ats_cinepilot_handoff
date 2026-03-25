# Local Setup (Windows 11)

## 1. venv

```powershell
.\scripts\setup_venv.ps1
```

## 2. ATS telemetry plugin

필수 경로:

```text
D:\Steam\steamapps\common\American Truck Simulator\bin\win_x64\plugins\atssharedplugin64v2.dll
```

선택된 telemetry contract:

- mapping: `SCSTelemetrySharedv2_ats`
- design note: `docs/SHARED_MEMORY_V2_DESIGN.md`

## 3. control plugin

현재 demo는 module steering을 쓰기 때문에 control plugin도 필요하다.

필수 파일:

```text
D:\Steam\steamapps\common\American Truck Simulator\bin\win_x64\plugins\scs_sdk_controller.dll
C:\workspaces\python_workspace\_ext\scs-sdk-controller\scscontroller.py
```

현재 repo helper:

- `scripts/install_scs_control_plugin.ps1`
- `scripts/patch_scs_control_plugin.py`

중요:

- plugin source는 callback context patch가 필요했다
- 현재 demo는 patched DLL 기준이다

## 4. current demo sink

현재 선택된 sink는 `hybrid`다.

- steering / blinkers: module
- throttle / brake: keyboard

이건 `configs/demo_active_corridor.yaml`에 드러나 있다.

## 5. config checks

```powershell
.\.venv\Scripts\ats-cinepilot check-config --config configs\demo_active_corridor.yaml
.\.venv\Scripts\ats-cinepilot check-config --config configs\profiles\replay_demo.yaml
```

## 6. live probes

telemetry:

```powershell
.\.venv\Scripts\python scripts\inspect_telemetry.py --config configs\demo_active_corridor.yaml --frames 3 --require-ready
```

controls:

```powershell
.\.venv\Scripts\python scripts\inspect_controls.py --config configs\demo_active_corridor.yaml --dry-run --require-ready
```

## 7. current known-good demo command

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_demo_active_corridor.ps1 -ShadowSteps 20 -ActiveSteps 80 -ActiveCountdownSeconds 8
```

## 8. operator caveats

- ATS 창은 foreground여야 한다
- drivable state여야 한다
- keyboard longitudinal은 background child process보다 direct run / human-run helper가 더 안정적이었다

## 9. 아직 미해결인 것

- module longitudinal(`aforward` / `abackward`)이 실제로 왜 안 먹는지
- general Active Mode setup
- route-aware wider corridor setup
