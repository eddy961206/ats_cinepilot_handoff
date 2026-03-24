# Local Setup (Windows 11)

## 1. 가상환경

```powershell
.\scripts\setup_venv.ps1
```

이번 세션에서도 실제로 성공했다.

## 2. 현재 선택된 live telemetry 경로

이 저장소가 지금 우선 지원하는 경로는 **MOZA shared memory v2**다.

- plugin DLL: `atssharedplugin64v2.dll`
- mapping name: `SCSTelemetrySharedv2_ats`
- probe config: `configs/live_probe_moza_shared_memory.yaml`
- 설계 메모: `docs/SHARED_MEMORY_V2_DESIGN.md`

RenCloud `Local\SCSTelemetry` 경로는 여전히 참고용이지만, 이 머신에서 첫 live validation과 300-step shadow를 통과한 경로는 아니다.

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

### dense local graph export
- local dense graph는 `_ext/trucksim_maps_repo`를 쓴다.
- Windows에선 `parser` native addon 빌드 때문에 Visual Studio C++ Build Tools가 필요하다.

```powershell
winget install --id Microsoft.VisualStudio.2022.BuildTools --exact --accept-package-agreements --accept-source-agreements --override "--wait --quiet --norestart --nocache --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended"
cd C:\workspaces\python_workspace\_ext\trucksim_maps_repo
npm install
```

중요:
- 이 repo는 `npm install` 마지막 symlink postinstall이 `EPERM`으로 죽을 수 있다.
- 그래도 `cityhash.node`, `gdeflate.node`, `tsx`가 생겼으면 `scripts/export_local_dense_graph.py`는 동작한다.

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
.\.venv\Scripts\python scripts\inspect_telemetry.py --config configs\live_probe_moza_shared_memory.yaml --frames 8
```

이 스크립트는 이제 아래를 보여준다.

- ATS 실행 여부
- plugin DLL 경로
- mapping visibility
- decode 성공 여부
- sampled frame별 update token / speed / rpm / gear / throttle / pose
- `pose_source`, `pose_frame`, `heading_source`
- `absolute_heading`, `anchor_heading`, `anchor_locked`
- stale/layout failure 분류

이번 세션의 실제 결과:

- ATS 실행 중
- `SCSTelemetrySharedv2_ats` visible
- decode 성공
- `pose_source=authoritative_absolute`
- `pose_frame=anchored_local`
- `anchor_locked=yes`
- `telemetry status: telemetry ready`

## 6. raw capture / offset 분석

capture:

```powershell
.\.venv\Scripts\python scripts\capture_shared_memory_v2.py --config configs\live_probe_moza_shared_memory.yaml --seconds 6 --hz 10 --delay 3 --label straight_absolute_anchor
```

analysis:

```powershell
.\.venv\Scripts\python scripts\analyze_shared_memory_v2_capture.py --input data\captures\shared_memory_v2 --inspect 285:f64 --inspect 293:f64 --inspect 301:f64
```

현재 채택한 absolute pose 계약:
- `285:f64` -> `world_x`
- `293:f64` -> `world_y`
- `301:f64` -> `world_z`

## 7. replay smoke

```powershell
.\.venv\Scripts\ats-cinepilot run --config configs\profiles\replay_demo.yaml --mode shadow --steps 5
```

이번 세션에서도 실제로 성공했다.

## 8. live shadow smoke / longer run

smoke:

```powershell
.\.venv\Scripts\ats-cinepilot run --config configs\live_probe_moza_shared_memory.yaml --mode shadow --steps 30
```

longer run:

```powershell
.\.venv\Scripts\ats-cinepilot run --config configs\live_probe_moza_shared_memory.yaml --mode shadow --steps 300
```

이번 세션의 실제 결과:

- startup summary 출력 확인
- live telemetry ingest 성공
- step log 출력 확인
- recorder 파일 생성 확인: `data/logs/live_probe_moza_shadow.jsonl`
- 300-step 샘플에서 `safety=NONE` 300/300
- `match_confidence` 최소값 `1.00`
- `cross_track_error_m` 최대값 `0.046`

중요:
- 지금 성공은 **authoritative absolute pose + anchored-local toy-graph matching bring-up 성공**이다.
- 아직 실제 ATS global road graph 정렬이 끝났다는 뜻은 아니다.

## 9. dense local graph export

```powershell
.\.venv\Scripts\python scripts\export_local_dense_graph.py --config configs\live_probe_ats_real_graph.yaml --config configs\profiles\replay_ab_straight_light_turn.yaml --parser-output-dir "data\maps\trucksim_parser\ats_local" --geojson-output-dir "data\maps\trucksim_geojson\ats_local_region" --output-cache "data\maps\cache\ats_usa_region_dense_local_geojson_8km.json" --radius-m 8000
```

이번 세션의 실제 결과:

- export 성공
- `node_count = 2143`
- `edge_count = 4312`
- `graph_source = trucksim_local_geojson_region`
- `alignment_mode = ats_absolute_identity`
- runtime config: `configs/live_probe_ats_dense_local_graph.yaml`

## 10. controls probe

```powershell
.\.venv\Scripts\python scripts\inspect_controls.py --config configs\default.yaml --dry-run
```

이번 세션 기준으로는 아직 아래 상태다.

- `scscontroller` module 없음
- control plugin DLL 없음
- Active Mode 검증 금지
