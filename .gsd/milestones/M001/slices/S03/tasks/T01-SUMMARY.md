---
id: T01
parent: S03
milestone: M001
provides:
  - Unified `train_baseline` payload contract for Men/Women with split metrics and feature snapshot
key_files:
  - mania_pipeline/scripts/03_lgbm_train.py
  - mania_pipeline/tests/test_lgbm_train_metrics_contract.py
  - .gsd/milestones/M001/slices/S03/S03-PLAN.md
  - .gsd/DECISIONS.md
  - .gsd/STATE.md
key_decisions:
  - D013: `train_baseline` returns `(model, payload)` and enforces deterministic single-class AUC signaling via `auc_reason`.
patterns_established:
  - Single shared split-metrics helper computes canonical `Train/Val/Test` metrics for both genders.
observability_surfaces:
  - `train_baseline(...)[1]['metrics_by_split'][split]['auc_reason']`
  - Runtime inspection via `run_metadata.json -> stage_outputs.train.metrics.*` (currently nested under existing T02-incomplete keys)
duration: 0h50m
verification_result: passed
completed_at: 2026-03-14T18:23:38+03:00
blocker_discovered: false
---

# T01: Refactor `03_lgbm_train.py` into unified split-metrics core for both genders

**Refactored `03_lgbm_train.py` to return a contract payload (`metrics_by_split`, `feature_snapshot`, `best_iteration`) for both genders and added a test that locks canonical split metrics + deterministic single-class AUC behavior.**

## What Happened

- `mania_pipeline/scripts/03_lgbm_train.py` refactored with a unified helper core:
  - Added `CANONICAL_SPLITS = ("Train", "Val", "Test")` and shared split-metric helpers.
  - Added `_compute_split_metrics(...)` + `_compute_metrics_by_split(...)` so Men/Women both use the same evaluation logic.
  - Added `_safe_auc(...)` policy:
    - empty split → `auc=None`, `auc_reason="split_empty"`
    - single-class split → `auc=None`, `auc_reason="single_class_target:<class>"`
    - normal case → float AUC and `auc_reason=None`
  - Updated `train_baseline` return shape from `(model, test_brier)` to `(model, payload)` where payload includes:
    - `gender`
    - `metrics_by_split` (`Train`/`Val`/`Test` with `brier`, `logloss`, `auc`, `auc_reason`, `row_count`)
    - `feature_snapshot` (`feature_columns`, `feature_count`)
    - `best_iteration`
- Added `mania_pipeline/tests/test_lgbm_train_metrics_contract.py`:
  - Contract test for both Men/Women payload schema parity.
  - Canonical split labels asserted against `split_leakage_contracts.ALLOWED_SPLIT_LABELS`.
  - Explicit `metrics_by_split['Test']` presence + row-count binding.
  - Single-class test split case asserts deterministic `auc=None` and `auc_reason="single_class_target:1"`.
- Updated GSD tracking artifacts:
  - Marked T01 complete in `S03-PLAN.md`.
  - Appended decision D013 in `DECISIONS.md`.
  - Updated `STATE.md` recent decision + next action to T02.

## Verification

### Task-level verification (T01)
- ✅ `./venv/Scripts/python -m pytest mania_pipeline/tests/test_lgbm_train_metrics_contract.py`
  - Result: `2 passed`

### Slice-level verification commands (executed per contract, partial expected at T01)
- ❌ `./venv/Scripts/python -m pytest mania_pipeline/tests/test_lgbm_train_metrics_contract.py mania_pipeline/tests/test_run_pipeline_s03_eval_contract.py mania_pipeline/tests/test_notebook_execution_path_guard.py`
  - Failure reason: `test_run_pipeline_s03_eval_contract.py` does not exist yet (T02), `test_notebook_execution_path_guard.py` does not exist yet (T03).
- ✅ `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_cli.py mania_pipeline/tests/test_run_pipeline_split_leakage_gate.py`
  - Result: `5 passed`
- ✅ `./venv/Scripts/python mania_pipeline/scripts/run_pipeline.py --seed 42 --run-label s03_unified_eval_smoke`
  - Result: run succeeded end-to-end.
- ❌ `./venv/Scripts/python -c "... metrics_table/side_by_side_summary asserts ..."`
  - Failure reason: `eval_report.json` lacks `metrics_table` (expected until T02 wiring).

### Observability impact verification
- ✅ Verified new payload surface exists in runtime metadata using:
  - `./venv/Scripts/python -c "... print train payload keys ..."`
- Confirmed `stage_outputs.train.metrics.men_test_brier` currently contains dict payload with keys:
  - `best_iteration`, `feature_snapshot`, `gender`, `metrics_by_split`
- Confirmed test split metrics include explicit AUC diagnostics keys:
  - `auc`, `auc_reason`, `brier`, `logloss`, `row_count`

## Diagnostics

- Inspect train payload contract quickly:
  - `./venv/Scripts/python -c "import json, pathlib; run_root=pathlib.Path('mania_pipeline/artifacts/runs'); run_dir=max([p for p in run_root.iterdir() if p.is_dir()], key=lambda p:p.stat().st_mtime_ns); md=json.loads((run_dir/'run_metadata.json').read_text(encoding='utf-8')); print(md['stage_outputs']['train'])"`
- Contract-level AUC edge diagnosis lives at:
  - `payload['metrics_by_split'][<split>]['auc_reason']`

## Deviations

- None.

## Known Issues

- `run_pipeline.py::stage_train` still expects old scalar naming (`men_test_brier`/`women_test_brier`) and now receives payload dicts in those slots. This is non-blocking for T01 but requires T02 wiring.
- `eval_report.json` still missing `metrics_table` and `side_by_side_summary` until T02.
- Notebook execution-path guard test is not present yet (T03 scope).

## Files Created/Modified

- `mania_pipeline/scripts/03_lgbm_train.py` — unified split-metrics helper core, deterministic AUC reason policy, new `(model, payload)` return contract.
- `mania_pipeline/tests/test_lgbm_train_metrics_contract.py` — locks Men/Women unified payload schema and single-class AUC reason behavior.
- `.gsd/milestones/M001/slices/S03/S03-PLAN.md` — marked T01 as complete.
- `.gsd/DECISIONS.md` — appended D013 train payload contract decision.
- `.gsd/STATE.md` — updated recent decisions and next action (T02).
