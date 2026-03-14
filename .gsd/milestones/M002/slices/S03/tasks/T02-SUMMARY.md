---
id: T02
parent: S03
milestone: M002
provides:
  - Governance decision report wiring in eval output plus artifact-stage required enforcement.
key_files:
  - mania_pipeline/scripts/run_pipeline.py
  - mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py
  - mania_pipeline/tests/test_run_pipeline_s07_submission_contract.py
key_decisions:
  - `governance_decision_report_json` is a required artifact in canonical artifact contract.
patterns_established:
  - Every new eval sub-report is mirrored to eval output and required by artifact contract.
observability_surfaces:
  - governance_decision_report.json
  - stage_outputs.eval_report.governance_decision
duration: ~20m
verification_result: passed
completed_at: 2026-03-15
blocker_discovered: false
---

# T02: Wire decision report and artifact requirement

**Wired governance decision report into eval payload and enforced it via artifact contract.**

## What Happened

- Added `governance_decision` block to stage eval return and `eval_report.json`.
- Added `governance_decision_report_json` to `stage_artifact` required artifact paths.
- Updated S06/S07 fixture contexts to include governance decision report path.

## Verification

- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py mania_pipeline/tests/test_run_pipeline_s07_submission_contract.py -q` ✅

## Diagnostics

- Missing decision report now appears as artifact contract fail-fast with explicit missing artifact name.

## Deviations

none

## Known Issues

none

## Files Created/Modified

- `mania_pipeline/scripts/run_pipeline.py` — decision report wiring + artifact requirement.
- `mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py` — fixture sync.
- `mania_pipeline/tests/test_run_pipeline_s07_submission_contract.py` — fixture sync.
