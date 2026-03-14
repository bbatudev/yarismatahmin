---
id: T01
parent: S02
milestone: M002
provides:
  - Deterministic calibration selector helpers with reason-coded availability and regime-aware method ordering.
key_files:
  - mania_pipeline/scripts/run_pipeline.py
  - mania_pipeline/tests/test_run_pipeline_m002_s02_calibration_policy_contract.py
key_decisions:
  - Candidate selection is Val-Brier driven with regime-based default fallback when improvement is below threshold.
patterns_established:
  - Availability-first policy evaluation (`status/reason`) before selection.
observability_surfaces:
  - calibration_policy.by_gender.<gender>.candidate_methods
  - calibration_policy.by_gender.<gender>.selection_reason
duration: ~40m
verification_result: passed
completed_at: 2026-03-15
blocker_discovered: false
---

# T01: Deterministic regime-aware selector helpers

**Added deterministic policy helpers that evaluate and select calibration methods with explicit reasons.**

## What Happened

- Added policy constants and helper functions for:
  - probability scoring bundle (Brier/LogLoss/AUC/ECE/WMAE),
  - method calibration transforms (`none`, `platt`, `isotonic`),
  - dominant regime detection and regime-based method order,
  - gender-level policy output with `selected_method`, `selection_reason`, and candidate statuses.
- Added S02 contract tests covering low-sample unavailable behavior and stage-level policy contract emission.

## Verification

- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_m002_s02_calibration_policy_contract.py -q` ✅

## Diagnostics

- Inspect selection reasoning from `calibration_policy.by_gender.<gender>.selection_reason`.

## Deviations

none

## Known Issues

- Thresholds are static baseline values; adaptive tuning deferred to later slices.

## Files Created/Modified

- `mania_pipeline/scripts/run_pipeline.py` — policy helper implementation.
- `mania_pipeline/tests/test_run_pipeline_m002_s02_calibration_policy_contract.py` — selector contract tests.
