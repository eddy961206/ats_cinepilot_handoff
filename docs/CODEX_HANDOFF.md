# CODEX HANDOFF

이 문서는 로컬 codex 구현 에이전트가 가장 먼저 읽어야 한다.

## 너의 역할

너는 이 저장소의 **실현체/구현체 에이전트**다.
이 저장소는 설계와 스캐폴드를 제공한다.
너는 사용자 PC에서:

- 설치
- 외부 플러그인 연결
- ATS 실행 중 실험
- 로그 수집
- 캘리브레이션
- 디버깅
- 반복 수정

을 담당한다.

## 절대 우선순위

1. telemetry bridge를 실제로 살아있게 만들 것
2. control sink를 실제로 게임에 연결할 것
3. shadow mode를 먼저 안정화할 것
4. active mode는 그 다음
5. neural lane model은 마지막

## 하지 말 것

- 처음부터 end-to-end CNN 자율주행으로 뛰지 말 것
- map matching이 흔들리는 상태에서 active mode를 열지 말 것
- HUD 파서 하드코딩만으로 문제를 해결하려고 하지 말 것
- 테스트 없이 large refactor 하지 말 것

## 첫 번째 작업 체크리스트

### A. 외부 결선
- 텔레메트리 plugin 선택
- 제어 plugin 선택
- map export 도구 선택

### B. smoke tests
- `scripts/inspect_telemetry.py`
- `scripts/inspect_controls.py --dry-run`
- `scripts/export_map.py`
- `scripts/calibrate_hud.py`

### C. shadow mode 성공 기준
- 텔레메트리 10분 이상 안정
- matcher edge hopping 거의 없음
- HUD route mask가 실제 빨간 길 위주로만 잡힘
- steering command가 극단적으로 튀지 않음
- safety disengage가 너무 자주 일어나지 않음

## 구현 순서

### Step 1
`bridge/scs_telemetry.py`
- 실제 plugin 스키마에 맞게 field mapping 확정
- stale detection 검증

### Step 2
`bridge/scs_controls.py`
- `scscontroller` 또는 다른 control plugin과 실제 필드명 매핑
- dry-run / active-run 분리

### Step 3
`map/adapters/*.py`
- 사용자가 선택한 exporter JSON을 internal graph cache로 변환

### Step 4
`scripts/calibrate_hud.py`
- 실제 ATS 1.58 widget layout에 맞게 preset 보정
- player icon / labels / city text 간섭 줄이기

### Step 5
`matcher`, `planner`, `controller`
- 로그 기반으로 gain 튜닝
- first stable highway run 달성

## acceptance criteria

### milestone 1
- telemetry read OK
- control write OK
- map cache load OK

### milestone 2
- shadow mode 5분 안정
- false disengage 빈도 낮음

### milestone 3
- highway active mode 가능
- exit ramp 일부 성공

## 구현 철학

- confidence 기반
- 안전 해제 우선
- replay 가능한 실험
- 작은 변경 / 빠른 검증
- 모듈 경계 유지
