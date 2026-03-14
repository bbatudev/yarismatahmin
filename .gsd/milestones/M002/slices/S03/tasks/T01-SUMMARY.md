---
id: T01
parent: S03
milestone: M002
provides:
  - Gender-level governance decision fusion from ablation + drift + calibration policy evidence.
key_files:
  - mania_pipeline/scripts/run_pipeline.py
  - mania_pipeline/tests/test_run_pipeline_m002_s03_governance_decision_contract.py
key_decisions:
  - Decision set fixed to `tighten_features|apply_calibration_policy|monitor_drift|hold_baseline` with aggregate mapping.
patterns_established:
  - Reason-coded multi-evidence bundle as first-class decision payload.
observability_surfaces:
  - governance_decision.by_gender.<gender>.decision
  - governance_decision.by_gender.<gender>.reason_codes
duration: ~35m
verification_result: passed
completed_at: 2026-03-15
blocker_discovered: false
---

# T01: Governance decision fusion helpers

**Implemented multi-evidence governance decision helpers and contract test coverage.**

## What Happened

- Added helper functions to extract ablation test deltas, drift alert signals, and calibration policy outcomes.
- Added deterministic decision/confidence generation per gender and aggregate decision rollup.
- Added S03 contract test to validate emitted decision schema and allowed decision domains.

## Verification

- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_m002_s03_governance_decision_contract.py -q` ✅

## Diagnostics

- Decision reasoning can be inspected from `reason_codes` + `evidence_bundle` in the new payload.

## Deviations

none

## Known Issues

- Confidence formula is heuristic baseline and may need retuning after S04 coupling.

## Files Created/Modified

- `mania_pipeline/scripts/run_pipeline.py` — governance decision fusion helpers.
- `mania_pipeline/tests/test_run_pipeline_m002_s03_governance_decision_contract.py` — decision contract tests.
