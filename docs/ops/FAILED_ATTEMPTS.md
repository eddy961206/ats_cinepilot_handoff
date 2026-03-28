# Failed Attempts

## 2026-03-29 — Dense baseline stability is not reproducible by helper alone

- failed hypothesis:
  - current dense helper만으로 similar-quality dense run이 반복 재현될 것이다
- what happened:
  - same helper가 끝까지는 돌았지만 `MATCH_LOST`가 크게 늘고 `cte_max`도 나빠졌다
- do not repeat unless:
  - 시작 위치 / runtime fit / artifact 비교를 함께 기록할 수 있을 때만
- note:
  - future agents should not assume yesterday's best dense run numbers are automatically reproducible

## 2026-03-29 — Do not use raw checked-in dense graph observer run as dense demo fitness evidence

- failed hypothesis:
  - `configs/cv_observer_dense_corridor.yaml`만으로 dense corridor qualification까지 같이 판단할 수 있다
- what happened:
  - observer run은 overlay/artifacts에는 성공했지만 runtime fit 없이 checked-in graph를 바로 보니까 `MATCH_LOST`가 계속 났다
- do not repeat unless:
  - 목적이 pure overlay validation일 때만
- note:
  - dense demo fitness는 반드시 `fit_demo_dense_corridor.py`를 거친 runtime contract/run으로 판단해야 한다
