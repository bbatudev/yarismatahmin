---
id: T02
parent: S04
milestone: M003
provides:
  - Contract test coverage for readiness statuses and failure-path report persistence.
key_files:
  - mania_pipeline/tests/test_run_pipeline_m003_s04_submission_readiness_contract.py
key_decisions:
  - Readiness test suite must cover blocked path with persisted report artifact.
patterns_established:
  - Gate-failure tests assert both raised error and diagnostic artifact existence.
observability_surfaces:
  - readiness status + blocking_checks assertions
duration: ~25m
verification_result: passed
completed_at: 2026-03-15
blocker_discovered: false
---

# T02: Readiness contract tests

**Added readiness contract tests for caution, ready, and blocked decision paths.**

## What Happened

- Added new S04 contract test file.
- Covered three key readiness outcomes:
  - caution: submission not requested
  - ready: gates pass + submission valid
  - blocked: regression failure path with persisted readiness report
- Re-ran impacted artifact/submission test suites.

## Verification

- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_m003_s04_submission_readiness_contract.py mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py mania_pipeline/tests/test_run_pipeline_s07_submission_contract.py -q` ✅

## Diagnostics

- Blocked path contract asserts readiness report exists even when stage raises.

## Deviations

none

## Known Issues

none

## Files Created/Modified

- `mania_pipeline/tests/test_run_pipeline_m003_s04_submission_readiness_contract.py`
