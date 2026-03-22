# Shared Memory V2 Design Note

## 목적

ATS 1.58에서 **첫 실제 live Shadow Mode**를 가장 빨리 검증하기 위해, 이 저장소는 현재 이 머신에서 실제로 보인 MOZA telemetry mapping을 우선 지원한다.

## 선택한 계약

- producer plugin: `atssharedplugin64v2.dll`
- selected mapping name: `SCSTelemetrySharedv2_ats`
- observed mapping size: `4096` bytes
- header guard:
  - `raw[1:4] == b"ats"` 이어야 함
  - buffer 길이는 최소 `768` bytes 이상이어야 함

## 현재 decode하는 필드

이 offset들은 2026-03-22 로컬 ATS 런타임과 live trace에서 확인한 값만 사용한다.

- `44`: `state_code` 후보
  - 값이 상황에 따라 `0.0` / `2.0`로 바뀌는 건 확인했지만, authoritative paused flag로는 아직 미확정
- `333`: `velocity_x_mps`
- `357`: `velocity_z_mps`
- `445`: `speed_mps`
- `449`: `engine_rpm`
- `453`: `gear`
- `457`: `displayed_gear`
- `461`: `throttle`
- `507`: `speed_limit_kph` 후보
- `544`: `route_distance_km` 후보
- `548`: `route_time_min` 후보

## 의도적으로 안 믿는 것

- `296`은 초기에 tick 후보로 봤지만, 정지 상태에서 안정적으로 증가하지 않아서 runtime freshness 기준으로는 폐기했다.
- absolute world `x/z`는 아직 확정 못 했다.

## runtime 전략

- `TelemetryFrame.game_tick`에는 authoritative game tick 대신 `crc32(raw_mapping)` 기반 **update token**을 넣는다.
- freshness는 이 update token 변화 여부로 판단한다.
- `pose.world_x/world_z`는 absolute map 좌표가 아니라, `velocity_x/velocity_z` 적분 기반의 **relative pose**다.
- `yaw_rad`는 planar velocity 방향에서 추정한다.

## validation 전략

1. `inspect_telemetry.py`로 mapping visibility 확인
2. decode guard 통과 여부 확인
3. sampled frames에서 update token 변화 확인
4. `ats-cinepilot run --config configs/live_probe_moza_shared_memory.yaml --mode shadow ...` 실행

## failure modes

- `mapping missing`
  - ATS가 아직 world state가 아니거나 plugin이 실제로 mapping을 안 열었을 수 있음
- `unsupported layout`
  - 다른 plugin/version이 같은 이름을 쓰지만 offset이 다를 수 있음
- `stale/non-updating`
  - mapping은 보이지만 live 값 갱신이 멈춘 상태
- `relative pose only`
  - 현재 shadow run은 absolute map alignment가 아니라 상대 pose로 돈다

## 현재 결론

- `SCSTelemetrySharedv2_ats` direct reader는 로컬에서 구현/검증됐다.
- 첫 live Shadow Mode run도 로컬에서 성공했다.
- 아직 미해결인 핵심은 absolute pose 계약 확정과, 그 뒤 control path 검증이다.
