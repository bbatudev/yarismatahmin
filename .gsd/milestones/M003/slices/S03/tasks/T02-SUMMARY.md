---
id: T02
parent: S03
milestone: M003
provides:
  - Ensemble payload wiring in eval output and artifact required-file contract.
key_files:
  - mania_pipeline/scripts/run_pipeline.py
  - mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py
  - mania_pipeline/tests/test_run_pipeline_s07_submission_contract.py
  - mania_pipeline/tests/test_run_pipeline_m002_s04_policy_gate_contract.py
key_decisions:
  - `ensemble_report_json` is treated as required artifact once S03 is active.
patterns_established:
  - Contract evolution by updating existing fixture contexts instead of weakening required-path checks.
observability_surfaces:
  - run_metadata.stage_outputs.eval_report.ensemble
duration: ~30m
verification_result: passed
completed_at: 2026-03-15
blocker_discovered: false
---

# T02: Eval/artifact wiring for ensemble contract

**Wired ensemble surface into eval outputs and artifact contract, then updated compatibility tests.**

## What Happened

- Added `ensemble` payload to `eval_report.json` and `stage_eval_report` return contract.
- Added `ensemble_report_json` to artifact required paths.
- Updated S06/S07/M002-S04 stage_artifact fixture contexts to include ensemble report stubs.

## Verification

- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py mania_pipeline/tests/test_run_pipeline_s07_submission_contract.py mania_pipeline/tests/test_run_pipeline_m002_s04_policy_gate_contract.py -q` ✅

## Diagnostics

- Missing ensemble artifact now surfaces via: `artifact contract failed: missing required artifacts -> ensemble_report_json`.

## Deviations

none

## Known Issues

none

## Files Created/Modified

- `mania_pipeline/scripts/run_pipeline.py` — eval/artifact wiring.
- `mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py` — fixture update.
- `mania_pipeline/tests/test_run_pipeline_s07_submission_contract.py` — fixture update.
- `mania_pipeline/tests/test_run_pipeline_m002_s04_policy_gate_contract.py` — fixture update.
