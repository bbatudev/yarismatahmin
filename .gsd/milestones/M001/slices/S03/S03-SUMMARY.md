---
id: S03
parent: M001
milestone: M001
provides:
  - Unified Men/Women training-eval core with canonical split metrics table and side-by-side test summary, enforced through script-only training authority.
requires:
  - slice: S02
    provides: feature stage split/leakage gate payload (`stage_outputs.feature.gates.{men,women}`) and canonical stage lifecycle
affects:
  - S04
  - S05
key_files:
  - mania_pipeline/scripts/03_lgbm_train.py
  - mania_pipeline/scripts/run_pipeline.py
  - mania_pipeline/scripts/03_model_training.ipynb
  - mania_pipeline/tests/test_lgbm_train_metrics_contract.py
  - mania_pipeline/tests/test_run_pipeline_s03_eval_contract.py
  - mania_pipeline/tests/test_notebook_execution_path_guard.py
  - mania_pipeline/tests/test_run_pipeline_cli.py
  - mania_pipeline/tests/test_run_pipeline_split_leakage_gate.py
  - .gsd/REQUIREMENTS.md
  - .gsd/milestones/M001/M001-ROADMAP.md
  - .gsd/PROJECT.md
  - .gsd/STATE.md
key_decisions:
  - D013: `train_baseline` payload contract (`metrics_by_split`, `feature_snapshot`, deterministic `auc_reason`)
  - D014: train stage hard-requires feature gate pass and eval report is emitted from canonical `stage_outputs.train`
  - D015: notebook training authority drift blocked by pytest pattern guard over notebook code cells
patterns_established:
  - Shared split-metrics helper and payload schema used identically by Men and Women tracks
  - Canonical `eval_report.json` normalization pattern (`metrics_table` + `side_by_side_summary`) sourced from `stage_outputs.train`
  - Script-first authority enforcement via executable guard test (not documentation-only policy)
observability_surfaces:
  - mania_pipeline/artifacts/runs/<run_id>/run_metadata.json -> stage_outputs.train.{genders,metrics_by_split,feature_snapshot,best_iteration,models}
  - mania_pipeline/artifacts/runs/<run_id>/eval_report.json -> metrics_table, side_by_side_summary
  - mania_pipeline/artifacts/runs/<run_id>/stage_events.jsonl -> stage lifecycle + failure diagnostics
  - ./venv/Scripts/python -m pytest mania_pipeline/tests/test_notebook_execution_path_guard.py
  - ./venv/Scripts/python -c "...S03 contract asserts..."
drill_down_paths:
  - .gsd/milestones/M001/slices/S03/tasks/T01-SUMMARY.md
  - .gsd/milestones/M001/slices/S03/tasks/T02-SUMMARY.md
  - .gsd/milestones/M001/slices/S03/tasks/T03-SUMMARY.md
duration: 2h03m
verification_result: passed
completed_at: 2026-03-14T18:45:54+03:00
---

# S03: Unified Men/Women Eval Core + Single Execution Path Enforcement

**Shipped a single canonical Men/Women training-eval contract (Train/Val/Test × Brier/LogLoss/AUC + side-by-side test summary) and technically closed notebook-side training authority.**

## What Happened

S03 unified the model-eval core and closed dual-authority drift in three linked changes.

- T01 refactored `03_lgbm_train.py` so `train_baseline(...)` now returns `(model, payload)` for both genders through the same helper path. Payload contract includes:
  - `metrics_by_split` for canonical splits (`Train`, `Val`, `Test`) with `brier`, `logloss`, `auc`, `auc_reason`, `row_count`
  - `feature_snapshot` (`feature_columns`, `feature_count`)
  - `best_iteration`
  - deterministic AUC null signaling for empty/single-class splits.
- T02 rewired `run_pipeline.py` train/eval stages:
  - `stage_train` now fails fast unless `stage_outputs.feature.gates.{men,women}.pass == True`
  - per-gender model outputs and split metrics persist under `stage_outputs.train`
  - `stage_eval_report` emits normalized `metrics_table` and `side_by_side_summary` from canonical train payloads.
- T03 demoted notebook authority:
  - `03_model_training.ipynb` replaced with artifact-analysis/reporting notebook
  - new regression guard `test_notebook_execution_path_guard.py` fails if notebook code cells reintroduce training/persistence primitives.

Result: S03 demo contract now exists on real runtime artifacts, and notebook/script divergence is enforced by executable checks.

## Verification

All slice-level checks from the plan were rerun and passed:

- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_lgbm_train_metrics_contract.py mania_pipeline/tests/test_run_pipeline_s03_eval_contract.py mania_pipeline/tests/test_notebook_execution_path_guard.py`
  - `8 passed`
- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_cli.py mania_pipeline/tests/test_run_pipeline_split_leakage_gate.py`
  - `5 passed`
- `./venv/Scripts/python mania_pipeline/scripts/run_pipeline.py --seed 42 --run-label s03_unified_eval_smoke`
  - succeeded (`run_id=20260314T154225Z_s03_unified_eval_smoke`)
- `./venv/Scripts/python -c "...S03 contract asserts..."`
  - `S03 contract ok: 20260314T154225Z_s03_unified_eval_smoke`

Observability surfaces confirmed on latest run:

- `run_metadata.json -> stage_outputs.train` includes `genders`, `metrics_by_split`, `feature_snapshot`, `best_iteration`, `models`.
- `eval_report.json` includes 6-row `metrics_table` (Men/Women × Train/Val/Test) and `side_by_side_summary` test deltas.
- `stage_events.jsonl` present and populated for stage lifecycle diagnostics.

## Requirements Advanced

- R002 — S02 gate payload is now hard-enforced as a train precondition in canonical runtime (prevents gate-bypass execution paths).

## Requirements Validated

- R003 — Notebook/script parity validated by notebook authority demotion + guardrail test blocking training/persistence primitives.
- R005 — Separate Men/Women model tracks validated by unified shared core producing separate per-gender train artifacts/payloads.
- R006 — Standard metrics + side-by-side summary validated by canonical `eval_report.json` schema and runtime assertions.
- R019 — Single execution path enforcement validated by script-first authority plus executable notebook drift guard.

## New Requirements Surfaced

- none

## Requirements Invalidated or Re-scoped

- none

## Deviations

none

## Known Limitations

- Calibration outputs (bins, ECE/W-MAE, drift summary) are not part of S03; deferred to S04.
- Feature governance/ablation ledger is not part of S03; deferred to S05.
- Reproducibility tolerance and regression gates are not yet enforced; deferred to S06.

## Follow-ups

- S04 should consume `stage_outputs.train.metrics_by_split` as the authoritative source for calibration/drift calculations.
- S05 should use `feature_snapshot` persisted in `stage_outputs.train` as baseline feature namespace evidence.

## Files Created/Modified

- `mania_pipeline/scripts/03_lgbm_train.py` — Unified Men/Women train payload contract with deterministic split-metric/AUC diagnostics.
- `mania_pipeline/scripts/run_pipeline.py` — Gate-preconditioned train stage + eval report table/summary emission.
- `mania_pipeline/scripts/03_model_training.ipynb` — Replaced with reporting-only notebook (no training/persistence authority).
- `mania_pipeline/tests/test_lgbm_train_metrics_contract.py` — Payload schema and split-metric contract tests.
- `mania_pipeline/tests/test_run_pipeline_s03_eval_contract.py` — New orchestrator eval contract + train precondition tests.
- `mania_pipeline/tests/test_notebook_execution_path_guard.py` — Notebook authority drift guard.
- `mania_pipeline/tests/test_run_pipeline_cli.py` — Updated CLI contract assertions for new train payload schema.
- `.gsd/REQUIREMENTS.md` — R003/R005/R006/R019 moved to validated with execution proof notes.
- `.gsd/milestones/M001/M001-ROADMAP.md` — S03 marked complete.
- `.gsd/PROJECT.md` — Current-state section refreshed for post-S03 reality.
- `.gsd/STATE.md` — Active slice/phase and requirement counters refreshed.

## Forward Intelligence

### What the next slice should know
- `eval_report.json` already has normalized split-level rows; S04 can compute calibration/drift without touching raw train scripts.
- `auc_reason` is now the stable diagnostic for single-class/empty split behavior; downstream quality logic should preserve it.

### What's fragile
- Notebook guard relies on pattern matching in code cells — effective for current primitives, but must be updated if modeling/persistence APIs change.

### Authoritative diagnostics
- `mania_pipeline/artifacts/runs/<run_id>/run_metadata.json` — single source for gate pass state and per-gender train outputs.
- `mania_pipeline/artifacts/runs/<run_id>/eval_report.json` — canonical machine-readable eval contract for downstream slices.

### What assumptions changed
- “Notebook training authority can be controlled by convention” — replaced with CI-enforced technical guard (`test_notebook_execution_path_guard.py`).
