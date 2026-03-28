# Experiment Log

## 2026-03-29T00:27:00+09:00 — Dense Demo Baseline Reproduction

- objective:
  - current dense curated active baseline이 아직 살아있는지 확인
- hypothesis:
  - telemetry/control/demo helper는 그대로 동작할 것이다
- branch/commit:
  - `codex/cv-observer-handoff-harness`
  - base `main@6eb557371a4806595f4e4fbfa0c28356367bcfd4`
- config(s):
  - `configs/demo_active_dense_corridor.yaml`
- command(s):
  - `.\.venv\Scripts\python.exe scripts\inspect_telemetry.py --config configs\demo_active_dense_corridor.yaml --frames 3 --require-ready`
  - `.\.venv\Scripts\python.exe scripts\inspect_controls.py --config configs\demo_active_dense_corridor.yaml --dry-run --require-ready`
  - `powershell -ExecutionPolicy Bypass -File scripts\run_demo_active_dense_corridor.ps1 -ShadowSteps 12 -ActiveSteps 140 -ActiveCountdownSeconds 3`
- artifact path(s):
  - `data/logs/demo_active_dense_corridor.jsonl`
  - `data/runtime/demo_dense_curated_corridor.runtime.yaml`
  - `data/maps/cache/demo_dense_curated_corridor.runtime.json`
- outcome:
  - partial
- interpretation:
  - telemetry/control readiness는 통과했다
  - dense helper도 끝까지 돌았다
  - 하지만 best run보다 훨씬 나빴고 `MATCH_LOST`가 `145`까지 치솟았다
  - current truck placement / runtime fit / bootstrap drift 영향이 다시 확인됐다
- next step:
  - handoff harness를 먼저 만들고, 그 다음 CV observer overlay를 얹는다
- repeat only if:
  - 다음 phase에서 CV observer 전후 비교 baseline이 다시 필요할 때만

## 2026-03-29T00:48:00+09:00 — Live CV Observer Overlay on Dense Corridor

- objective:
  - ATS live capture에서 lane/vehicle observer와 human-visible overlay/artifact path를 검증
- hypothesis:
  - classical lane observer는 current corridor image에서 usable overlay를 만들 것이다
  - vehicle detector는 적어도 live pipeline 자체는 정상 동작할 것이다
- branch/commit:
  - `codex/cv-observer-handoff-harness`
  - base `main@6eb557371a4806595f4e4fbfa0c28356367bcfd4`
- config(s):
  - `configs/cv_observer_dense_corridor.yaml`
- command(s):
  - `powershell -ExecutionPolicy Bypass -File scripts\run_cv_observer_dense_corridor.ps1 -Steps 80`
- artifact path(s):
  - `data/artifacts/cv/observer_dense_corridor/observer_overlay.mp4`
  - `data/artifacts/cv/observer_dense_corridor/frame_00001.jpg`
  - `data/logs/cv_observer_dense_corridor.cv.jsonl`
- outcome:
  - success
- interpretation:
  - lane overlay는 live run에서 안정적으로 생성됐다
  - `lane_detected=80/80`, `lane_conf=[1.000,1.000]`
  - 이번 run에서는 `lead_detected=0`이라 live vehicle evidence는 못 얻었다
  - observer config는 runtime-fit corridor가 아니라 checked-in dense graph를 바로 보므로 graph-side safety 평가는 이 실험 목적이 아니다
- next step:
  - CV를 dense active helper에 얹어서 실제 demo run에서도 artifact를 남긴다
- repeat only if:
  - lane overlay regression이 의심되거나 live vehicle target 장면을 확보했을 때만

## 2026-03-29T00:49:00+09:00 — Dense Active Demo With CV Enabled

- objective:
  - 기존 dense curated active demo에 CV overlay/artifact/guard를 보수적으로 얹어 live run을 검증
- hypothesis:
  - CV layer를 켜도 planner/control primary path는 그대로 유지될 것이다
  - dense demo safety cage가 여전히 주도권을 가진 채 active run이 가능할 것이다
- branch/commit:
  - `codex/cv-observer-handoff-harness`
  - base `main@6eb557371a4806595f4e4fbfa0c28356367bcfd4`
- config(s):
  - `configs/demo_active_dense_corridor_with_cv.yaml`
  - `data/runtime/demo_dense_curated_corridor.runtime.yaml`
- command(s):
  - `powershell -ExecutionPolicy Bypass -File scripts\run_demo_active_dense_corridor_with_cv.ps1 -ShadowSteps 8 -ActiveSteps 80 -ActiveCountdownSeconds 3`
- artifact path(s):
  - `data/logs/demo_active_dense_corridor_with_cv.jsonl`
  - `data/logs/demo_active_dense_corridor_with_cv.cv.jsonl`
  - `data/artifacts/cv/demo_active_dense_corridor/observer_overlay.mp4`
  - `data/runtime/demo_dense_curated_corridor.runtime.yaml`
  - `data/maps/cache/demo_dense_curated_corridor.runtime.json`
- outcome:
  - success
- interpretation:
  - active run은 `NONE=48`을 유지했고 `cte_max=0.039`로 corridor 안에 머물렀다
  - CV artifact는 동시에 생성됐다
  - 이번 run에서도 `lead_detected=0`이라 CV guard trigger는 없었다
  - 그래서 이번 세션 결론은 “CV observer + overlay + disengage-only guard plumbing is real”, not “visual risk braking verified”
- next step:
  - live traffic가 있는 장면에서 vehicle detection/lead guard evidence를 모은다
  - barrier/road-edge는 후순위로 둔다
- repeat only if:
  - lead vehicle scene 확보 또는 guard threshold 조정이 필요할 때만

## 2026-03-29T00:59:00+09:00 — Short Dense Active + CV Rerun For Post-Review Smoke

- objective:
  - review fix 이후에도 live dense+CV path가 안 깨졌는지 짧게 재검증
- hypothesis:
  - fail-closed observer handling과 pinned model contract fix는 normal path를 깨지지 않을 것이다
- branch/commit:
  - `codex/cv-observer-handoff-harness`
  - base `main@6eb557371a4806595f4e4fbfa0c28356367bcfd4`
- config(s):
  - `configs/demo_active_dense_corridor_with_cv.yaml`
  - `data/runtime/demo_dense_curated_corridor.runtime.yaml`
- command(s):
  - `powershell -ExecutionPolicy Bypass -File scripts\run_demo_active_dense_corridor_with_cv.ps1 -ShadowSteps 4 -ActiveSteps 40 -ActiveCountdownSeconds 3`
- artifact path(s):
  - `data/logs/demo_active_dense_corridor_with_cv.jsonl`
  - `data/logs/demo_active_dense_corridor_with_cv.cv.jsonl`
  - `data/artifacts/cv/demo_active_dense_corridor/observer_overlay.mp4`
- outcome:
  - partial
- interpretation:
  - code path는 안 깨졌다
  - dense active repeatability는 다시 나빠져 `MATCH_LOST=44`가 나왔다
  - 대신 `lead_detected=2`, `lead_conf_max=0.567`까지는 잡혀서 live vehicle positive evidence는 일부 생겼다
  - 아직 guard threshold `0.60`을 넘는 confident lead target은 못 봤다
- next step:
  - traffic가 더 명확한 장면에서 lead guard evidence를 모은다
- repeat only if:
  - live vehicle threshold calibration을 다시 만질 때만
