---
id: T01
parent: S05
milestone: M001
provides:
  - Deterministic governance ledger generation from canonical train payload with gender-aware filtering and machine-readable evidence.
key_files:
  - mania_pipeline/scripts/feature_governance.py
  - mania_pipeline/scripts/run_pipeline.py
  - mania_pipeline/tests/test_feature_governance_ledger.py
  - mania_pipeline/tests/test_run_pipeline_s05_governance_contract.py
  - mania_pipeline/tests/test_feature_governance_ablation.py
key_decisions:
  - D022: `default_action` is importance/rank driven (`drop|candidate|keep`) and women ledger excludes men-only features.
patterns_established:
  - Eval-stage artifact extension pattern: compute governance payload in `stage_eval_report`, emit CSV artifact, and mirror summary/path under `eval_report.json` + `stage_outputs.eval_report`.
observability_surfaces:
  - `run_metadata.json.stage_outputs.eval_report.governance`
  - `eval_report.json.governance`
  - `governance_ledger.csv`
duration: ~1h 20m
verification_result: passed
completed_at: 2026-03-14
blocker_discovered: false
---

# T01: Build governance ledger contract from canonical train payload

**Shipped deterministic governance ledger generation (schema + domain constrained) into canonical eval stage, with machine-readable evidence and women-side men-only filtering.**

## What Happened

- Pre-flight observability gaps were fixed first:
  - `.gsd/milestones/M001/slices/S05/S05-PLAN.md` verification list now includes a diagnostics/failure-surface check.
  - `.gsd/milestones/M001/slices/S05/tasks/T01-PLAN.md` now includes `## Observability Impact`.
- Added new module: `mania_pipeline/scripts/feature_governance.py`.
  - Feature grouping helper (`infer_feature_group`).
  - Deterministic `default_action` derivation (`keep|drop|candidate`) from baseline importance/rank.
  - JSON evidence builder (stable sort order, split metrics snapshot embedded).
  - Women ledger guard: men-only feature set is explicitly skipped for `gender=women`.
  - Governance summary helper (`row_count`, `default_action_counts`, `group_counts`).
- Wired governance into `mania_pipeline/scripts/run_pipeline.py::stage_eval_report`.
  - Loads governance module via cached script loader.
  - Collects per-gender model importance vectors alongside existing calibration scoring.
  - Builds and writes `governance_ledger.csv` in run directory.
  - Publishes governance payload into both:
    - `eval_report.json.governance`
    - `stage_outputs.eval_report.governance`
- Added tests:
  - `mania_pipeline/tests/test_feature_governance_ledger.py` (schema/domain/determinism/women-filter contract).
  - `mania_pipeline/tests/test_run_pipeline_s05_governance_contract.py` (orchestrator ledger wiring assertion).
  - `mania_pipeline/tests/test_feature_governance_ablation.py` (xfail placeholder for T02 so slice verification file set exists from first task).
- Appended decision row `D022` to `.gsd/DECISIONS.md`.

## Verification

### Task-level commands (required by T01)
- ✅ `./venv/Scripts/python -m pytest mania_pipeline/tests/test_feature_governance_ledger.py`
- ✅ `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_s05_governance_contract.py -k ledger`

### Slice-level verification commands (run in T01; partial pass expected)
- ✅ `./venv/Scripts/python -m pytest mania_pipeline/tests/test_feature_governance_ledger.py mania_pipeline/tests/test_feature_governance_ablation.py mania_pipeline/tests/test_run_pipeline_s05_governance_contract.py`
  - Result: `4 passed, 1 xfailed` (`test_feature_governance_ablation.py` intentionally pending T02)
- ✅ `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_cli.py mania_pipeline/tests/test_run_pipeline_s04_calibration_contract.py`
- ✅ `./venv/Scripts/python mania_pipeline/scripts/run_pipeline.py --seed 42 --run-label s05_governance_smoke`
- ❌ `./venv/Scripts/python -c "... gov['artifacts']['ablation_report_json'] ... executed_group_count ..."`
  - Expected fail in T01 (`KeyError: 'ablation_report_json'`) because ablation artifact is T02 scope.
- ❌ `./venv/Scripts/python -c "... summary['skipped_groups'] ..."`
  - Expected fail in T01; `skipped_groups` is ablation diagnostics surface (T02).

## Diagnostics

- Inspect ledger rows: `mania_pipeline/artifacts/runs/<run_id>/governance_ledger.csv`
- Inspect eval payload mirror: `mania_pipeline/artifacts/runs/<run_id>/eval_report.json` → `governance`
- Inspect metadata mirror: `mania_pipeline/artifacts/runs/<run_id>/run_metadata.json` → `stage_outputs.eval_report.governance`
- Evidence field is machine-readable JSON string; parse per-row `evidence` to inspect rank/importance/split metrics.

## Deviations

- Added `mania_pipeline/tests/test_feature_governance_ablation.py` as an xfail placeholder in T01 so slice-level verification file set exists from the first slice task.

## Known Issues

- Ablation contract surfaces (`ablation_report_json`, `executed_group_count`, `skipped_groups`) are not implemented yet; corresponding slice verification asserts fail until T02/T03.

## Files Created/Modified

- `mania_pipeline/scripts/feature_governance.py` — governance ledger builders, policy derivation, summary helpers.
- `mania_pipeline/scripts/run_pipeline.py` — eval stage governance artifact generation + payload wiring.
- `mania_pipeline/tests/test_feature_governance_ledger.py` — ledger schema/domain/determinism tests.
- `mania_pipeline/tests/test_run_pipeline_s05_governance_contract.py` — eval-stage ledger wiring test.
- `mania_pipeline/tests/test_feature_governance_ablation.py` — pending xfail scaffold for T02.
- `.gsd/milestones/M001/slices/S05/S05-PLAN.md` — added diagnostics verification step and marked T01 done.
- `.gsd/milestones/M001/slices/S05/tasks/T01-PLAN.md` — added `Observability Impact` section.
- `.gsd/DECISIONS.md` — appended D022 governance policy decision.
