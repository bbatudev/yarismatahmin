---
id: T02
parent: S03
milestone: M001
provides:
  - Canonical `run_pipeline.py` now enforces feature-gate preconditions before train and publishes Men/Women split metrics as `metrics_table` + `side_by_side_summary` in `eval_report.json`
key_files:
  - mania_pipeline/scripts/run_pipeline.py
  - mania_pipeline/tests/test_run_pipeline_s03_eval_contract.py
  - mania_pipeline/tests/test_run_pipeline_cli.py
  - .gsd/milestones/M001/slices/S03/S03-PLAN.md
  - .gsd/DECISIONS.md
  - .gsd/STATE.md
key_decisions:
  - D014: Orchestrator contract now requires feature gate pass before train and uses `stage_outputs.train` as the single source for eval table/summary emission.
patterns_established:
  - `stage_outputs.train.metrics_by_split.{men,women}.{Train,Val,Test}` is the canonical source for normalized eval reporting.
observability_surfaces:
  - `mania_pipeline/artifacts/runs/<run_id>/run_metadata.json -> stage_outputs.train`
  - `mania_pipeline/artifacts/runs/<run_id>/eval_report.json -> metrics_table, side_by_side_summary`
  - Train gate-precondition failures surface via `stage_events.jsonl` with explicit `blocking_rule` in `error.message`
duration: 0h35m
verification_result: passed
completed_at: 2026-03-14T18:31:35+03:00
blocker_discovered: false
---

# T02: Wire canonical train/eval stages to publish metrics table + side-by-side summary

**Updated canonical train/eval wiring so run artifacts now expose normalized split metrics and Men-vs-Women test comparison, with train blocked unless feature gates pass.**

## What Happened

- `mania_pipeline/scripts/run_pipeline.py`
  - `stage_train` now hard-checks `stage_outputs.feature.gates.{men,women}.pass` before loading the train module (fail-fast on missing/failing gates).
  - `stage_train` now consumes T01 payloads from `train_baseline(...)` and persists per-gender artifacts under a structured contract:
    - `genders.{men,women}.model_path`
    - `genders.{men,women}.metrics_by_split`
    - `genders.{men,women}.feature_snapshot`
    - `genders.{men,women}.best_iteration`
    - plus mirrored top-level `models`, `metrics_by_split`, `feature_snapshot`, `best_iteration`.
  - `stage_eval_report` now normalizes per-gender split metrics into `metrics_table` rows with `gender/split/brier/logloss/auc` and emits `side_by_side_summary` for Test split deltas.

- `mania_pipeline/tests/test_run_pipeline_s03_eval_contract.py` (new)
  - Added contract tests for:
    - train payload persistence shape,
    - train precondition fail-fast behavior,
    - eval report schema (`metrics_table`, `side_by_side_summary`),
    - full `main()` lifecycle stopping at `train` when feature gate is blocking.
  - Sandboxed stage-train unit tests by patching `PIPELINE_DIR` to `tmp_path` to avoid polluting repository artifact files during pytest runs.

- `mania_pipeline/tests/test_run_pipeline_cli.py`
  - Updated stubbed `train` stage payload to reflect the new train schema.
  - Added success-path assertions that `run_metadata.json -> stage_outputs.train` carries `metrics_by_split`, `feature_snapshot`, and `models`.

- GSD tracking updates:
  - Marked T02 complete in `S03-PLAN.md`.
  - Appended decision D014 in `DECISIONS.md`.
  - Updated `STATE.md` next action to T03.

## Verification

### Task-level verification (T02)
- ✅ `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_s03_eval_contract.py mania_pipeline/tests/test_run_pipeline_cli.py mania_pipeline/tests/test_run_pipeline_split_leakage_gate.py`
  - Result: `9 passed`
- ✅ `./venv/Scripts/python mania_pipeline/scripts/run_pipeline.py --seed 42 --run-label s03_unified_eval_smoke`
  - Result: run succeeded end-to-end.
- ✅ `./venv/Scripts/python -c "import json, pathlib; r=max([p for p in pathlib.Path('mania_pipeline/artifacts/runs').iterdir() if p.is_dir()], key=lambda p:p.stat().st_mtime_ns); report=json.loads((r/'eval_report.json').read_text(encoding='utf-8')); assert report['metrics_table']; assert 'side_by_side_summary' in report; print('ok', r.name)"`
  - Result: `ok <run_id>`.

### Slice-level verification commands (executed per contract; partial expected at T02)
- ❌ `./venv/Scripts/python -m pytest mania_pipeline/tests/test_lgbm_train_metrics_contract.py mania_pipeline/tests/test_run_pipeline_s03_eval_contract.py mania_pipeline/tests/test_notebook_execution_path_guard.py`
  - Failure reason: `mania_pipeline/tests/test_notebook_execution_path_guard.py` does not exist yet (T03 scope).
- ✅ `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_cli.py mania_pipeline/tests/test_run_pipeline_split_leakage_gate.py`
  - Result: `5 passed`.
- ✅ `./venv/Scripts/python mania_pipeline/scripts/run_pipeline.py --seed 42 --run-label s03_unified_eval_smoke`
  - Result: passed.
- ✅ `./venv/Scripts/python -c "import json, pathlib; run_root=pathlib.Path('mania_pipeline/artifacts/runs'); run_dir=max([p for p in run_root.iterdir() if p.is_dir()], key=lambda p:p.stat().st_mtime_ns); md=json.loads((run_dir/'run_metadata.json').read_text(encoding='utf-8')); report=json.loads((run_dir/'eval_report.json').read_text(encoding='utf-8')); gates=md['stage_outputs']['feature']['gates']; assert gates['men']['pass'] and gates['women']['pass']; table=report['metrics_table']; assert {'gender','split','brier','logloss','auc'}.issubset(table[0].keys()); side=report['side_by_side_summary']; assert {'men_test_brier','women_test_brier','delta_test_brier'}.issubset(side.keys()); print('S03 contract ok:', run_dir.name)"`
  - Result: `S03 contract ok: <run_id>`.

### Observability impact verification
- ✅ Verified `run_metadata.json -> stage_outputs.train` now contains `metrics_by_split` and `feature_snapshot` for both genders.
- ✅ Verified `eval_report.json` now contains normalized `metrics_table` and `side_by_side_summary`.
- ✅ Verified gate-precondition failure visibility via integration test asserting `train` failed event message includes blocking rule (`R006_FEATURE_GATE_REQUIRED`).

## Diagnostics

- Inspect latest train payload quickly:
  - `./venv/Scripts/python -c "import json, pathlib; run_root=pathlib.Path('mania_pipeline/artifacts/runs'); run_dir=max([p for p in run_root.iterdir() if p.is_dir()], key=lambda p:p.stat().st_mtime_ns); md=json.loads((run_dir/'run_metadata.json').read_text(encoding='utf-8')); print(md['stage_outputs']['train'].keys())"`
- Inspect latest eval report table + side summary:
  - `./venv/Scripts/python -c "import json, pathlib; run_root=pathlib.Path('mania_pipeline/artifacts/runs'); run_dir=max([p for p in run_root.iterdir() if p.is_dir()], key=lambda p:p.stat().st_mtime_ns); report=json.loads((run_dir/'eval_report.json').read_text(encoding='utf-8')); print(report['metrics_table'][0]); print(report['side_by_side_summary'])"`

## Deviations

- None.

## Known Issues

- `mania_pipeline/tests/test_notebook_execution_path_guard.py` is still missing; slice-level command including that file fails until T03 is completed.

## Files Created/Modified

- `mania_pipeline/scripts/run_pipeline.py` — Added train-stage gate precondition, persisted structured per-gender train payload, and generated normalized eval report table + side-by-side summary.
- `mania_pipeline/tests/test_run_pipeline_s03_eval_contract.py` — New contract tests for train/eval wiring and train gate fail-fast behavior.
- `mania_pipeline/tests/test_run_pipeline_cli.py` — Updated stubbed train payload and CLI metadata assertions for new train schema.
- `.gsd/milestones/M001/slices/S03/S03-PLAN.md` — Marked T02 as complete.
- `.gsd/DECISIONS.md` — Added D014 orchestrator contract decision.
- `.gsd/STATE.md` — Updated recent decision and next action to T03.
