---
id: T02
parent: S02
milestone: M002
provides:
  - Policy artifact wiring in eval output and artifact-stage required contract enforcement.
key_files:
  - mania_pipeline/scripts/run_pipeline.py
  - mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py
  - mania_pipeline/tests/test_run_pipeline_s07_submission_contract.py
key_decisions:
  - `calibration_policy_report_json` is required in artifact contract like other eval reports.
patterns_established:
  - New eval sub-report integration requires fixture alignment in S06/S07 contract tests.
observability_surfaces:
  - calibration_policy_report.json
  - stage_outputs.eval_report.calibration_policy
duration: ~25m
verification_result: passed
completed_at: 2026-03-15
blocker_discovered: false
---

# T02: Wire policy artifact and enforce artifact contract

**Wired calibration policy report into canonical outputs and enforced it as a required artifact.**

## What Happened

- Added `calibration_policy` block to `eval_report.json` and stage eval return payload.
- Added `calibration_policy_report_json` into artifact contract required artifact map.
- Updated S06/S07 artifact/submission fixture contexts to include policy report path so contract tests remain aligned.

## Verification

- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py mania_pipeline/tests/test_run_pipeline_s07_submission_contract.py -q` ✅

## Diagnostics

- Missing policy report now surfaces as artifact-stage fail-fast in `artifact_contract_report.json.missing_artifacts`.

## Deviations

none

## Known Issues

none

## Files Created/Modified

- `mania_pipeline/scripts/run_pipeline.py` — eval/artifact policy wiring.
- `mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py` — required artifact fixture sync.
- `mania_pipeline/tests/test_run_pipeline_s07_submission_contract.py` — required artifact fixture sync.
