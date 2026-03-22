# Architecture

## 목표

American Truck Simulator에서 내비게이션을 따라가며 경치를 구경할 수 있을 정도로 안정적인 자동주행을 만든다.

v1 목표는 아래다.

- 고속도로 위주
- 기본 맵 또는 추출 가능한 맵 조합
- shadow mode부터 시작
- confidence가 낮으면 즉시 해제
- HUD는 **주 경로 소스가 아니라 분기 힌트 보조 소스**
- 딥러닝 기반 차선 추정은 선택 사항

## 핵심 아이디어

```text
ATS
 ├─ Telemetry plugin/shared memory ──> telemetry bridge
 ├─ Control plugin/shared memory  <── input bridge
 └─ Game window capture           ──> HUD route provider

Map export JSON ──> graph adapter ──> road graph / spatial index

telemetry
  └─ pose matcher
      └─ route provider / fusion
          └─ preview planner
              ├─ lateral controller
              ├─ longitudinal controller
              └─ safety arbiter
                    └─ control sink
```

## 모듈 경계

### bridge/
게임과 통신하는 영역이다.

- `scs_telemetry.py`
- `scs_controls.py`
- `capture_dxcam.py`
- `capture_mss.py`
- `manual_override.py`

여기는 절대 경로 판단을 하면 안 된다.

### map/
도로 그래프, spatial index, pose matching.

### perception/
화면에서 HUD route line과 turn bias를 뽑는다.

### route/
HUD/direct/manual route hint를 하나의 인터페이스로 캡슐화한다.

### planner/
현재 edge + route hint를 받아 preview path와 speed target을 만든다.

### control/
preview path와 speed target을 실제 steering/throttle/brake로 변환한다.

### safety/
모든 출력 명령의 마지막 심사관이다.

### ops/
config, logging, replay, recorder.

### ui/
디버그 overlay.

## 상태 머신

```text
OFF -> CALIBRATING -> SHADOW -> ARMED -> ACTIVE
 \                               |
  \-> FAULT <---- DISENGAGING <-/
```

## v1 우선순위

1. telemetry 읽기
2. control write 경로 연결
3. map export -> internal graph cache
4. pose matching 안정화
5. HUD route widget calibration
6. shadow mode
7. active mode
8. junction handling
9. lane model / lead-vehicle model 같은 고급 기능

## 설계 원칙

- confidence가 낮으면 해제
- hard real-time 욕심내지 말고 replay 가능하게 만들기
- 로그 없이는 튜닝하지 않기
- map matching이 흔들리면 제어를 열지 않기
- active mode보다 shadow mode가 먼저
