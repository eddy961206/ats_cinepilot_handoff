# Plugin / Tool Options

이 저장소에는 외부 프로젝트의 코드를 번들하지 않았다.
대신 어떤 외부 프로젝트를 연결하면 좋은지 정리해뒀다.

## 1) 텔레메트리

### 공식 SCS Telemetry SDK
- 공식 문서:
  - https://modding.scssoft.com/wiki/Documentation/Engine/SDK/Telemetry
- 장점:
  - 장기적으로 가장 정석
  - input device 지원 언급도 있음
- 단점:
  - 직접 bridge를 만들면 초기 작업량이 있음

### RenCloud / shared-memory 계열 플러그인
- 예:
  - https://github.com/RenCloud/scs-sdk-plugin
  - https://github.com/truckermudgeon/scs-sdk-plugin
- 장점:
  - shared memory 경로 예시가 많음
- 단점:
  - 구조체 레이아웃과 버전 차이 확인 필요

### JSON wrapper 서비스
- 예:
  - scs telemetry JSON service 류
- 장점:
  - Python에서 빨리 붙이기 쉬움
- 단점:
  - 응답 스키마가 구현마다 다름

## 2) 입력 제어

### scs-sdk-controller
- https://github.com/ETS2LA/scs-sdk-controller
- 장점:
  - `Local\SCSControls` shared memory로 프로그램이 게임을 제어하도록 설계됨
- 권장:
  - v1 primary path

### keyboard / mouse / vJoy
- 장점:
  - 빨리 붙일 수 있음
- 단점:
  - 불안정, 포커스 영향 큼
  - 장시간 안정 주행에 불리

## 3) 맵 export

### truckermudgeon/maps
- https://github.com/truckermudgeon/maps
- 장점:
  - 기본 맵/DLC 중심으로 깔끔
- 단점:
  - 서드파티 map mod 지원이 약함

### ts-map
- https://github.com/dariowouters/ts-map
- 장점:
  - 1.58 support 표기
  - map mod loading 표기
- 단점:
  - 실제 사용하는 맵 조합마다 검증 필요

## 4) 화면 캡처

### DXcam
- https://github.com/ra1nty/DXcam
- 장점:
  - Windows Desktop Duplication 기반
  - 저지연 / 고FPS
- 권장:
  - primary capture backend

### MSS
- https://github.com/BoboTiG/python-mss
- 장점:
  - 단순하고 fallback으로 좋음

## 5) 추후 GPU 추론

### ONNX Runtime GPU
- https://onnxruntime.ai/docs/execution-providers/CUDA-ExecutionProvider.html
- 장점:
  - NVIDIA GPU에 붙이기 좋음

### TensorRT EP
- https://onnxruntime.ai/docs/execution-providers/TensorRT-ExecutionProvider.html
- 장점:
  - 속도가 중요해질 때 선택지
