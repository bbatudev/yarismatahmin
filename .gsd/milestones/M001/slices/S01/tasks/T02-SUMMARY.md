---
id: T02
parent: S01
milestone: M001
provides:
  - Canonical `run_pipeline` CLI that executes deterministic feature -> train -> eval_report -> artifact stages with run-scoped metadata/events and real Python-level stage wiring
key_files:
  - mania_pipeline/scripts/run_pipeline.py
  - mania_pipeline/scripts/03_lgbm_train.py
  - README.md
  - .gsd/milestones/M001/slices/S01/S01-PLAN.md
  - .gsd/DECISIONS.md
  - .gsd/STATE.md
key_decisions:
  - Added D009: dynamic import + absolute path rebinding for numeric-prefixed stage scripts so canonical orchestration remains deterministic regardless of caller cwd
patterns_established:
  - Stage lifecycle wrapper pattern: append `started` then `succeeded/failed` JSONL events per stage and stop immediately on first failure with non-zero exit
observability_surfaces:
  - `mania_pipeline/artifacts/runs/<run_id>/run_metadata.json`
  - `mania_pipeline/artifacts/runs/<run_id>/stage_events.jsonl`
  - `mania_pipeline/artifacts/runs/<run_id>/eval_report.json`
  - `mania_pipeline/artifacts/runs/<run_id>/artifact_manifest.json`
duration: 1h 30m
verification_result: passed
completed_at: 2026-03-14T14:27:48Z
blocker_discovered: false
---

# T02: Implement canonical `run_pipeline` CLI and real-stage wiring

**Implemented a production `run_pipeline.py` orchestrator that runs real feature/train/eval/artifact stages, persists run metadata + lifecycle JSONL events, and exits non-zero with machine-readable failure payload on stage errors.**

## What Happened

- Created `mania_pipeline/scripts/run_pipeline.py` with required contract seam:
  - `build_run_context(seed=...)`
  - `main(argv=None)`
  - `CANONICAL_STAGES`
  - `STAGE_HANDLERS`
- Implemented argparse CLI options exactly as planned:
  - `--seed`
  - `--run-label`
  - `--artifacts-root`
- Implemented deterministic stage execution order:
  - `feature -> train -> eval_report -> artifact`
- Implemented structured lifecycle event writer (`stage_events.jsonl`) with contract fields for each event:
  - `stage`, `status`, `started_at`, `finished_at`, `duration_ms`, `error`
- Wired real stage logic via Python-level calls:
  - `02_feature_engineering.py::run_pipeline` for Men/Women feature generation and CSV persistence
  - `03_lgbm_train.py::{load_data, train_baseline}` for Men/Women training
- Added run-scoped outputs:
  - `run_metadata.json` (run context + status + stage outputs)
  - `eval_report.json` (seed, model paths, test Brier metrics)
  - `artifact_manifest.json` (run file inventory)
- Implemented failure behavior:
  - first failing stage writes `failed` event with structured error payload (`type`, `message`, traceback tail)
  - metadata marks `status=failed`, `failed_stage`, `error`
  - process returns non-zero
- Updated `README.md` with canonical command usage and artifact locations.
- Updated `03_lgbm_train.py` to accept `random_state` in `train_baseline(...)` so CLI seed is wired into training.
- Runtime bug found/fixed during smoke run:
  - First smoke run failed in `train` stage with Windows encoding error from Unicode box-drawing character (`'─'`) in training logs.
  - Replaced that output with ASCII dashes in `03_lgbm_train.py`; smoke run then passed end-to-end.

## Verification

- Contract tests:
  - `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_context_contract.py mania_pipeline/tests/test_run_pipeline_cli.py`
  - Result: **11 passed**
- Real canonical smoke run:
  - `./venv/Scripts/python mania_pipeline/scripts/run_pipeline.py --seed 42 --run-label s01_smoke`
  - Result: **passed**
  - Verified run dir created:
    - `mania_pipeline/artifacts/runs/20260314T142603Z_s01_smoke`
- Task-level artifact assertions:
  - `./venv/Scripts/python -c "from pathlib import Path; import json; d=sorted(Path('mania_pipeline/artifacts/runs').glob('*'))[-1]; m=json.loads((d/'run_metadata.json').read_text(encoding='utf-8')); e=[json.loads(x) for x in (d/'stage_events.jsonl').read_text(encoding='utf-8').splitlines() if x.strip()]; assert m['seed']==42; assert [x['stage'] for x in e if x['status']=='succeeded']==['feature','train','eval_report','artifact']; print('ok', d)"`
  - Result: **passed**
- Slice verification assertion:
  - `./venv/Scripts/python -c "from pathlib import Path; import json; runs=sorted(Path('mania_pipeline/artifacts/runs').glob('*')); assert runs, 'no run dir'; latest=runs[-1]; meta=json.loads((latest/'run_metadata.json').read_text(encoding='utf-8')); events=[json.loads(x) for x in (latest/'stage_events.jsonl').read_text(encoding='utf-8').splitlines() if x.strip()]; assert {'run_id','seed','git_commit','started_at','command','cwd'}.issubset(meta.keys()); ok=[e for e in events if e.get('status')=='succeeded']; assert [e['stage'] for e in ok]==['feature','train','eval_report','artifact']; print('S01 contract verified:', latest)"`
  - Result: **passed**

## Diagnostics

- Primary inspection surfaces:
  - `mania_pipeline/artifacts/runs/<run_id>/run_metadata.json`
  - `mania_pipeline/artifacts/runs/<run_id>/stage_events.jsonl`
- Latest successful run:
  - `mania_pipeline/artifacts/runs/20260314T142603Z_s01_smoke`
- Failure-path evidence also exists from first smoke attempt (`train` stage encoding error) under prior run directory with `failed` event + error payload.

## Deviations

- None.

## Known Issues

- Console output still shows mojibake for some Turkish characters under current Windows shell code page, but pipeline execution and orchestrator contracts pass.

## Files Created/Modified

- `mania_pipeline/scripts/run_pipeline.py` — canonical orchestrator CLI, stage lifecycle logging, run metadata persistence, real-stage wiring, failure handling.
- `mania_pipeline/scripts/03_lgbm_train.py` — seeded training hook (`random_state`) and ASCII-safe performance divider output.
- `README.md` — documented canonical command and run artifact locations.
- `.gsd/milestones/M001/slices/S01/S01-PLAN.md` — marked T02 completed (`[x]`).
- `.gsd/DECISIONS.md` — appended D009 runtime wiring decision.
- `.gsd/STATE.md` — updated active state and next action after T02 completion.
