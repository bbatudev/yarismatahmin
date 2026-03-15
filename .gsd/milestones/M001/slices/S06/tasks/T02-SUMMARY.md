---
id: T02
parent: S06
milestone: M001
provides:
  - Same commit+seed reproducibility tolerance gate with persisted report and breach failure semantics.
key_files:
  - mania_pipeline/scripts/run_pipeline.py
  - mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py
key_decisions:
  - D004: reproducibility tolerance remains |ΔBrier| <= 1e-4.
patterns_established:
  - Run-history lookup pattern over prior successful `run_metadata.json` entries.
observability_surfaces:
  - reproducibility_report.json
  - stage_outputs.artifact.reproducibility.status
duration: ~45m
verification_result: passed
completed_at: 2026-03-15
blocker_discovered: false
---

# T02: Implement reproducibility tolerance gate with same commit+seed baseline lookup

**Implemented reproducibility gate that compares Test Brier against the latest same commit+seed baseline and fails on tolerance breach.**

## What Happened

- Prior successful run metadata discovery helper eklendi.
- Current/baseline snapshot extraction helper’ı eklendi.
- `reproducibility_report.json` üretimi eklendi.
- Rule: same commit+seed baseline varsa `|ΔBrier| <= 1e-4` gender bazında enforce; breach fail.
- Baseline yoksa deterministic `skipped` + reason (`no_baseline_same_commit_seed`).

## Verification

- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py -k "repro"` ✅
- `./venv/Scripts/python mania_pipeline/scripts/run_pipeline.py --seed 42 --run-label s06_repro_check` ✅
- run assert: `reproducibility_report.json.status == 'passed'` ✅

## Diagnostics

- `mania_pipeline/artifacts/runs/<run_id>/reproducibility_report.json`
- `run_metadata.json -> stage_outputs.artifact.reproducibility`

## Deviations

none

## Known Issues

none

## Files Created/Modified

- `mania_pipeline/scripts/run_pipeline.py` — reproducibility evaluator + gate enforcement.
- `mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py` — reproducibility pass/fail/skip coverage.
