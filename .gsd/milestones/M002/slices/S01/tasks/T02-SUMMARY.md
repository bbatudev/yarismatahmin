---
id: T02
parent: S01
milestone: M002
provides:
  - Drift artifact emission (`drift_regime_report.json`) and eval/metadata wiring.
key_files:
  - mania_pipeline/scripts/run_pipeline.py
  - mania_pipeline/tests/test_run_pipeline_m002_s01_drift_contract.py
key_decisions:
  - Drift report is emitted from `stage_eval_report` to preserve canonical topology.
patterns_established:
  - Eval-stage artifact extension pattern reused for drift payload.
observability_surfaces:
  - drift_regime_report.json
  - eval_report.json.drift
  - run_metadata.json.stage_outputs.eval_report.drift
duration: ~25m
verification_result: passed
completed_at: 2026-03-15
blocker_discovered: false
---

# T02: Emit drift artifact and wire into eval/metadata contracts

**Implemented drift report artifact and mirrored its contract into eval_report and stage_outputs surfaces.**

## What Happened

- `drift_regime_report.json` generation added in `stage_eval_report`.
- `drift` block added to:
  - `eval_report.json`
  - `stage_outputs.eval_report` return payload.
- Artifact stage required-artifact contract updated to include `drift_regime_report_json`.
- Existing S06/S07 test fixtures were updated with drift payload to keep contract consistency.

## Verification

- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_m002_s01_drift_contract.py` ✅
- `./venv/Scripts/python -m pytest mania_pipeline/tests -q` ✅

## Diagnostics

- `drift_regime_report.json` is the authoritative drift artifact.

## Deviations

none

## Known Issues

none

## Files Created/Modified

- `mania_pipeline/scripts/run_pipeline.py` — drift artifact emission + payload wiring + artifact contract expansion.
- `mania_pipeline/tests/test_run_pipeline_m002_s01_drift_contract.py` — drift wiring assertions.
- `mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py` — fixture drift payload alignment.
- `mania_pipeline/tests/test_run_pipeline_s07_submission_contract.py` — fixture drift payload alignment.
