---
id: T01
parent: S01
milestone: M002
provides:
  - Deterministic drift summary and seed-regime segmentation helpers with reason-coded alerts.
key_files:
  - mania_pipeline/scripts/run_pipeline.py
  - mania_pipeline/tests/test_run_pipeline_m002_s01_drift_contract.py
key_decisions:
  - Use `SeedNum_diff` absolute bins for initial regimes (`close|medium|wide`).
patterns_established:
  - Drift helper pattern parallels calibration helper structure (split summary + sparse reason codes).
observability_surfaces:
  - drift alerts in `stage_outputs.eval_report.drift.alerts`
duration: ~35m
verification_result: passed
completed_at: 2026-03-15
blocker_discovered: false
---

# T01: Add deterministic drift summary helpers and regime segmentation

**Added split/regime drift helpers and reason-coded alert logic for canonical eval scoring.**

## What Happened

- Added drift constants and helper functions:
  - `_build_split_drift_summary`
  - `_seed_regime_from_diff`
  - `_build_test_regime_drift_summary`
  - `_build_gap_shift_alert`
- Wired helper usage into eval scoring loop for each gender/split.
- Added test coverage for helper behavior and regime bucket mapping.

## Verification

- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_m002_s01_drift_contract.py -k "helpers"` ✅

## Diagnostics

- Helper outputs are visible through drift payload in eval stage output.

## Deviations

none

## Known Issues

none

## Files Created/Modified

- `mania_pipeline/scripts/run_pipeline.py` — drift helpers + per-split/per-regime summary logic.
- `mania_pipeline/tests/test_run_pipeline_m002_s01_drift_contract.py` — helper contract assertions.
