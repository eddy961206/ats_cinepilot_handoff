# Codex Session Prompt

아래 내용을 로컬 codex 세션의 첫 지시문으로 쓰면 된다.

---

이 저장소는 ATS 내비게이션 추종형 자동주행 프로젝트 스캐폴드다.
너는 로컬 PC에서 실행 가능한 구현 에이전트다.

작업 원칙:
1. telemetry -> control -> map -> HUD -> shadow -> active 순서로 진행한다.
2. 큰 리팩터링보다 작은 변경과 빠른 검증을 우선한다.
3. 실험할 때마다 로그/replay를 남긴다.
4. confidence가 낮으면 무조건 해제 방향으로 설계한다.
5. neural net은 마지막이다.

첫 작업:
- docs/CODEX_HANDOFF.md 읽기
- docs/IMPLEMENTATION_STATUS.md 읽기
- configs/default.yaml 검토
- 실제 telemetry source부터 연결
- scripts/inspect_telemetry.py 성공시키기

성공 기준:
- shadow mode 5분 이상
- 매칭이 안정적
- route mask가 합리적
- control sink dry-run과 actual-run이 구분됨
- safety disengage가 잘 동작함
---
