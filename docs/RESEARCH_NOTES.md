# Research Notes

이 문서는 설계 판단 근거를 빠르게 넘겨주기 위한 메모다.

## 핵심 근거

### SCS Telemetry SDK
- 공식 문서:
  - https://modding.scssoft.com/wiki/Documentation/Engine/SDK/Telemetry
- 메모:
  - 텔레메트리 접근을 제공
  - 1.14부터 basic input devices 지원 언급
- 설계 영향:
  - 화면만 보는 구조보다 game state 활용이 더 안정적

### ATS 1.58 Route Advisor 변화
- 공식 블로그:
  - https://blog.scssoft.com/2026/02/american-truck-simulator-158-update.html
  - https://blog.scssoft.com/2026/02/the-new-route-advisor-why-and-how-its.html
- 메모:
  - Route Advisor가 widget-based로 재구성됨
- 설계 영향:
  - HUD 파서는 고정 좌표 하드코딩보다 preset + verification 구조가 필요

### ETS2LA
- https://ets2la.com/
- https://github.com/ETS2LA/scs-sdk-controller
- 메모:
  - direct in-game navigation route access 언급
  - road/prefab network 활용
  - control shared memory 사용
- 설계 영향:
  - 장기 목표는 route access / network 중심
  - v1은 HUD 보조 + graph 중심

### 공개 autopilot 힌트들
- ats-autopilot:
  - https://github.com/boris-ns/ats-autopilot
  - 차선 유지 위주, vJoy 기반
- ets2_autopilot2:
  - https://github.com/Hexus-One/ets2_autopilot2
  - HUD GPS 기반, pure pursuit
  - crossovers / roundabouts 취약
- ETSAuto:
  - https://github.com/Lyric0620/ETSAuto
  - ONNXRuntime / TensorRT / pure pursuit
  - ACC 없음, intersection 제약
- SelfDrivingATS:
  - https://github.com/djnugent/SelfDrivingATS
  - PID cruise control
  - minimap cue를 보조 입력으로 사용

## 최종 설계 결론

- telemetry는 필수
- map graph는 핵심
- HUD는 보조
- safety arbiter는 강하게
- shadow mode 없이 active mode로 가지 말 것
