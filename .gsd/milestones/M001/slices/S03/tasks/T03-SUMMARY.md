---
id: T03
parent: S03
milestone: M001
provides:
  - Notebook authority is demoted to canonical artifact analysis/reporting only, with a regression guard that blocks reintroduction of notebook-side training/persistence primitives.
key_files:
  - mania_pipeline/scripts/03_model_training.ipynb
  - mania_pipeline/tests/test_notebook_execution_path_guard.py
  - .gsd/milestones/M001/slices/S03/tasks/T03-PLAN.md
  - .gsd/milestones/M001/slices/S03/S03-PLAN.md
  - .gsd/DECISIONS.md
  - .gsd/STATE.md
key_decisions:
  - D015: Notebook training authority drift is enforced by a code-cell pattern guard in pytest (not convention-only).
patterns_established:
  - Parse notebook JSON code cells in tests and fail with cell index + line context when forbidden train/persist primitives appear.
observability_surfaces:
  - `./venv/Scripts/python -m pytest mania_pipeline/tests/test_notebook_execution_path_guard.py`
  - Guard failure payload includes `cell[index]`, matched pattern name, and offending line text.
  - Canonical runtime inspection remains `mania_pipeline/artifacts/runs/<run_id>/{run_metadata.json,eval_report.json}`.
duration: 0h38m
verification_result: passed
completed_at: 2026-03-14T18:39:43+03:00
blocker_discovered: false
---

# T03: Enforce script-only training authority by demoting notebook + adding guardrail test

**Replaced `03_model_training.ipynb` with a canonical artifact-report notebook and added a guard test that fails if notebook code cells reintroduce training or model persistence primitives.**

## What Happened

- `mania_pipeline/scripts/03_model_training.ipynb`
  - Fully replaced prior dual-authority notebook with a reporting-only notebook.
  - Added explicit script-first authority statement at notebook entry:
    - training authority: `run_pipeline.py` + `03_lgbm_train.py`
    - notebook role: canonical artifact analysis/reporting only.
  - Notebook now only:
    - discovers latest run under `mania_pipeline/artifacts/runs`
    - reads `run_metadata.json` and `eval_report.json`
    - displays `metrics_table` and `side_by_side_summary`
    - renders a simple Test Brier by gender chart.

- `mania_pipeline/tests/test_notebook_execution_path_guard.py` (new)
  - Added notebook guard tests:
    - asserts script-first authority markdown note is present.
    - parses notebook JSON code cells and fails on forbidden patterns:
      - `LGBMClassifier(` / `LGBMRegressor(`
      - `.fit(`
      - `joblib.dump(`
      - `pickle.dump(`
      - `lgb.train(`
  - Failure messages include cell index + line number + offending code fragment for fast diagnosis.

- Governance artifact updates:
  - Added `## Observability Impact` section to `.gsd/milestones/M001/slices/S03/tasks/T03-PLAN.md` (pre-flight requirement).
  - Marked T03 done in `S03-PLAN.md`.
  - Appended D015 to `.gsd/DECISIONS.md`.

## Verification

### Task-level verification (T03)
- ✅ `./venv/Scripts/python -m pytest mania_pipeline/tests/test_notebook_execution_path_guard.py`
  - Result: `2 passed`.

### Slice-level verification (final task, all required checks)
- ✅ `./venv/Scripts/python -m pytest mania_pipeline/tests/test_lgbm_train_metrics_contract.py mania_pipeline/tests/test_run_pipeline_s03_eval_contract.py mania_pipeline/tests/test_notebook_execution_path_guard.py`
  - Result: `8 passed`.
- ✅ `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_cli.py mania_pipeline/tests/test_run_pipeline_split_leakage_gate.py`
  - Result: `5 passed`.
- ✅ `./venv/Scripts/python mania_pipeline/scripts/run_pipeline.py --seed 42 --run-label s03_unified_eval_smoke`
  - Result: succeeded (`run_id=20260314T153830Z_s03_unified_eval_smoke`).
- ✅ `./venv/Scripts/python -c "import json, pathlib; run_root=pathlib.Path('mania_pipeline/artifacts/runs'); run_dir=max([p for p in run_root.iterdir() if p.is_dir()], key=lambda p:p.stat().st_mtime_ns); md=json.loads((run_dir/'run_metadata.json').read_text(encoding='utf-8')); report=json.loads((run_dir/'eval_report.json').read_text(encoding='utf-8')); gates=md['stage_outputs']['feature']['gates']; assert gates['men']['pass'] and gates['women']['pass']; table=report['metrics_table']; assert {'gender','split','brier','logloss','auc'}.issubset(table[0].keys()); side=report['side_by_side_summary']; assert {'men_test_brier','women_test_brier','delta_test_brier'}.issubset(side.keys()); print('S03 contract ok:', run_dir.name)"`
  - Result: `S03 contract ok: 20260314T153830Z_s03_unified_eval_smoke`.

## Diagnostics

- Re-run notebook authority guard:
  - `./venv/Scripts/python -m pytest mania_pipeline/tests/test_notebook_execution_path_guard.py`
- If guard fails, read assertion details for `cell[index]` + `pattern` + `line` and inspect the notebook JSON code cell sources.
- Inspect latest canonical artifacts:
  - `mania_pipeline/artifacts/runs/<latest_run_id>/run_metadata.json`
  - `mania_pipeline/artifacts/runs/<latest_run_id>/eval_report.json`

## Deviations

- None.

## Known Issues

- None.

## Files Created/Modified

- `mania_pipeline/scripts/03_model_training.ipynb` — Replaced with canonical run artifact analysis/reporting notebook; removed training/persistence authority.
- `mania_pipeline/tests/test_notebook_execution_path_guard.py` — Added regression guard for notebook training/persistence drift plus authority-note assertion.
- `.gsd/milestones/M001/slices/S03/tasks/T03-PLAN.md` — Added missing `## Observability Impact` section (pre-flight fix).
- `.gsd/milestones/M001/slices/S03/S03-PLAN.md` — Marked T03 complete.
- `.gsd/DECISIONS.md` — Added D015 (notebook authority drift guard policy).
- `.gsd/STATE.md` — Updated current state for post-T03 handoff.
