# Shared Memory V2 Design Note

## 목적

ATS 1.58에서 **실제 live telemetry를 앱 loop 안으로 안정적으로 넣고**, 그 위에 shadow map matching을 검증하기 위한 현재 지원 계약이다.

이 문서는 지금 로컬 머신에서 실제로 보인 mapping만 기준으로 적는다. 추정과 검증 완료를 섞지 않는다.

## 선택한 계약

- producer plugin: `atssharedplugin64v2.dll`
- selected mapping name: `SCSTelemetrySharedv2_ats`
- observed mapping size: `4096` bytes
- header guard:
  - `raw[1:4] == b"ats"` 이어야 함
  - buffer 길이는 최소 `768` bytes 이상이어야 함

## 현재 채택한 offset

이 값들은 2026-03-22 로컬 ATS 런타임, live probe, controlled capture에서 다시 확인했다.

- `44:f32` -> `state_code` 후보
- `285:f64` -> `world_x`
- `293:f64` -> `world_y`
- `301:f64` -> `world_z`
- `333:f32` -> `velocity_x_mps`
- `357:f32` -> `velocity_z_mps`
- `445:f32` -> `speed_mps`
- `449:f32` -> `engine_rpm`
- `453:u32` -> `gear`
- `457:u32` -> `displayed_gear`
- `461:f32` -> `throttle`
- `507:f32` -> `speed_limit_kph` 후보
- `544:f32` -> `route_distance_km` 후보
- `548:f32` -> `route_time_min` 후보

## absolute pose 검증 근거

controlled capture와 raw candidate scan에서 아래가 일관되게 나왔다.

- `285:f64`, `301:f64`는 움직임에 따라 smooth하게 변한다.
- `293:f64`는 거의 고정되고 작은 폭으로만 변해서 높이 축처럼 보인다.
- `285/301`의 변화량으로 계산한 speed가 실제 `speed_mps`와 비슷하게 나온다.
- 직진 샘플에서 start/end 기준:
  - `dx ~= -6.66`
  - `dz ~= -1.03`
  - `dt ~= 5.91`
  - absolute position 기반 speed `~= 1.14 m/s`
- 이 값은 live `speed_mps ~= 1.14`와 맞는다.

## yaw / heading 현재 결론

authoritative direct yaw offset은 아직 확정하지 않았다.

조사된 후보:
- `309:f32`
- `325:f32`

이 둘은 heading/turn과 상관이 있어 보이지만, 아직 계약으로 채택할 만큼 안전하게 설명되지 않는다.

그래서 현재 runtime heading 전략은 direct yaw field가 아니라 아래다.

1. absolute world position이 있을 때 `absolute_position_delta`를 우선 사용
2. delta 길이가 `absolute_heading_min_distance_m` 이상일 때만 새 heading으로 인정
3. 그 사이 프레임은 `absolute_position_hold`로 마지막 authoritative heading 유지
4. absolute position이 없을 때만 `velocity_direction`으로 fallback

현재 기본값:
- `absolute_heading_min_distance_m = 0.25`

## anchored-local 전략

현재 기본 map cache는 실제 ATS world graph가 아니라 toy graph다.

그래서 runtime은 아래 두 frame mode를 지원한다.

- `world_absolute`
  - raw absolute `world_x/world_z`를 그대로 노출
- `anchored_local`
  - 첫 absolute position을 local origin으로 잡고
  - 첫 valid `absolute_position_delta`가 나온 뒤에만 anchor heading을 lock하고
  - 그 뒤 absolute pose를 toy graph local frame으로 회전해서 노출

중요:
- `anchored_local`은 **bring-up / matcher 검증용 local frame**이지, ATS 글로벌 좌표와 실제 road graph가 정렬됐다는 뜻이 아니다.

## validation 전략

1. mapping visibility 확인

```powershell
.\.venv\Scripts\python scripts\inspect_telemetry.py --config configs\live_probe_moza_shared_memory.yaml --frames 8
```

2. raw capture 수집

```powershell
.\.venv\Scripts\python scripts\capture_shared_memory_v2.py --config configs\live_probe_moza_shared_memory.yaml --seconds 6 --hz 10 --delay 3 --label straight_absolute_anchor
```

3. candidate scan / offset 확인

```powershell
.\.venv\Scripts\python scripts\analyze_shared_memory_v2_capture.py --input data\captures\shared_memory_v2 --inspect 285:f64 --inspect 293:f64 --inspect 301:f64
```

4. live shadow run

```powershell
.\.venv\Scripts\ats-cinepilot run --config configs\live_probe_moza_shared_memory.yaml --mode shadow --steps 300
```

## 이 세션에서 실제 확인한 결과

- `inspect_telemetry.py`에서:
  - mapping visible
  - decode 성공
  - `pose_source=authoritative_absolute`
  - `pose_frame=anchored_local`
  - `anchor_locked=yes`
- 300-step live shadow에서:
  - `safety=NONE` 300/300
  - `match_confidence` 최소값 `1.00`
  - `cross_track_error_m` 최대값 `0.046`
- 직전 세션 대비:
  - 초기 `MATCH_LOST`가 사라짐
  - heading noise와 anchored-local drift가 크게 줄어듦

## failure modes

- `mapping missing`
  - ATS world state가 아니거나 plugin이 mapping을 아직 안 열었을 수 있음
- `unsupported layout`
  - 같은 이름을 쓰더라도 offset이 다른 다른 plugin/version일 수 있음
- `stale/non-updating`
  - mapping은 보이지만 update token이 바뀌지 않음
- `anchored_local_pending_heading`
  - absolute position은 읽혔지만 아직 heading lock 전이라 local frame이 provisional 상태
- `toy-graph alignment only`
  - 현재 성공은 toy graph local frame 기준 bring-up이지, true global map alignment가 아님

## 현재 결론

- `SCSTelemetrySharedv2_ats` direct reader는 로컬에서 구현/검증됐다.
- `285/293/301` absolute pose 계약은 현재 가장 안전한 선택이다.
- first valid absolute heading 이후 anchor를 lock하는 전략으로 live shadow stability가 실제로 개선됐다.
- 아직 미해결인 핵심은:
  - direct yaw field 확정 여부
  - 실제 ATS map graph와의 global alignment
  - 그 뒤 control path 검증
