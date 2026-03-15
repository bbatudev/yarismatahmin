---
id: T01
parent: S04
milestone: M002
provides:
  - Policy-aware regression fallback behavior with warning surface.
key_files:
  - mania_pipeline/scripts/run_pipeline.py
  - mania_pipeline/tests/test_run_pipeline_m002_s04_policy_gate_contract.py
key_decisions:
  - Calibration degradation may downgrade to warning only when governance policy confidence and improvement signals are strong.
patterns_established:
  - Gate strictness can be policy-conditioned while preserving explicit blocking rules.
observability_surfaces:
  - regression_gate_report.json.by_gender.<gender>.policy_gate
  - regression_gate_report.json.warnings
duration: ~35m
verification_result: passed
completed_at: 2026-03-15
blocker_discovered: false
---

# T01: Policy-aware regression fallback

**Added policy-conditioned fallback behavior to regression gate with explicit warning diagnostics.**

## What Happened

- Extended run snapshot extraction to include governance decision signals.
- Updated regression gate logic:
  - calibration degradation still evaluated,
  - fallback applies only under `apply_calibration_policy` + confidence threshold + positive improvement,
  - fallback results are marked as warnings with explicit reason.
- Added S04 contract test that proves fallback path and ensures gate status remains passed under valid fallback conditions.

## Verification

- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_m002_s04_policy_gate_contract.py -q` ✅

## Diagnostics

- Inspect `regression_gate_report.json.warnings` and per-gender `policy_gate.fallback_applied`.

## Deviations

none

## Known Issues

- Confidence threshold is heuristic and may need tuning with longer run history.

## Files Created/Modified

- `mania_pipeline/scripts/run_pipeline.py` — policy-aware regression logic.
- `mania_pipeline/tests/test_run_pipeline_m002_s04_policy_gate_contract.py` — fallback contract test.
