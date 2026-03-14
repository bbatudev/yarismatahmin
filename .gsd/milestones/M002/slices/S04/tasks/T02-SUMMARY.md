---
id: T02
parent: S04
milestone: M002
provides:
  - `policy_gate_report.json` emission and manifest/return wiring in artifact stage.
key_files:
  - mania_pipeline/scripts/run_pipeline.py
  - mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py
  - mania_pipeline/tests/test_run_pipeline_s07_submission_contract.py
key_decisions:
  - Final integration diagnostics should be persisted separately from regression report for operator clarity.
patterns_established:
  - New gate-control reports are surfaced both in artifact manifest contracts and stage return payload.
observability_surfaces:
  - policy_gate_report.json
  - artifact_manifest.json.contracts.policy_gate
duration: ~20m
verification_result: passed
completed_at: 2026-03-15
blocker_discovered: false
---

# T02: Policy gate report wiring

**Wired policy gate integration report into artifact manifest and stage return contracts.**

## What Happened

- Added `policy_gate_report.json` generation in `stage_artifact`.
- Added policy gate contract surface to artifact manifest contracts.
- Added `policy_gate` block to stage artifact return payload for metadata mirror visibility.
- Re-ran S06/S07 tests to ensure no contract regressions.

## Verification

- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py mania_pipeline/tests/test_run_pipeline_s07_submission_contract.py -q` ✅

## Diagnostics

- Policy-gate status and report path available at `stage_outputs.artifact.policy_gate`.

## Deviations

none

## Known Issues

none

## Files Created/Modified

- `mania_pipeline/scripts/run_pipeline.py` — policy gate report emission + contract wiring.
- `mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py` — compatibility verification.
- `mania_pipeline/tests/test_run_pipeline_s07_submission_contract.py` — compatibility verification.
