# Safety

게임 안에서의 자동주행이지만, 일부러 보수적으로 설계한다.

## hard disengage

- user override
- telemetry stale
- paused
- control sink unhealthy
- HUD signature invalid
- route confidence too low
- map match lost

## soft disengage

- cross-track error 누적
- heading error 누적
- branch ambiguity
- curvature overspeed
- prolonged steering saturation

## 운영 원칙

- active mode보다 shadow mode 시간이 더 길어야 한다
- 위험하면 멈추는 쪽으로
- “억지로 계속”보다 “즉시 해제”가 낫다
- AI traffic 대응은 v1 범위를 넘어가면 별도 과제로 분리
