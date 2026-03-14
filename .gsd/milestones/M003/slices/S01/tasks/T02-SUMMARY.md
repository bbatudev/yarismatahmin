---
id: T02
parent: S01
milestone: M003
provides:
  - CLI/context/stage_train profile propagation contract.
key_files:
  - mania_pipeline/scripts/run_pipeline.py
  - mania_pipeline/tests/test_run_pipeline_m003_s01_training_profile_contract.py
key_decisions:
  - Orchestrator uses `--training-profile` with default `baseline` and forwards to train stage.
patterns_established:
  - Backward-compatible stage_train call path for older stubs/modules without `profile` arg.
observability_surfaces:
  - `stage_outputs.train.training_profile`
  - `stage_outputs.train.genders.<gender>.training_profile`
duration: ~30m
verification_result: passed
completed_at: 2026-03-15
blocker_discovered: false
---

# T02: Wire training profile through canonical orchestrator

**Canonical orchestrator now carries training profile from CLI to train payload.**

## What Happened

- Added CLI arg: `--training-profile {baseline,quality_v1}`.
- Propagated profile into run context and `stage_train`.
- Extended train payload with top-level/gender-level profile metadata.
- Added compatibility fallback in `stage_train` for test stubs lacking `profile` arg.

## Verification

- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_m003_s01_training_profile_contract.py -q` ✅
- Regression checks: CLI + S03 eval tests ✅

## Diagnostics

- Profile is visible directly in run metadata under `stage_outputs.train`.

## Deviations

none

## Known Issues

none

## Files Created/Modified

- `mania_pipeline/scripts/run_pipeline.py` — profile wiring.
- `mania_pipeline/tests/test_run_pipeline_m003_s01_training_profile_contract.py` — contract tests.
