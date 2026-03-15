---
id: T01
parent: S01
milestone: M003
provides:
  - Named training profile support (`baseline`, `quality_v1`) in trainer.
key_files:
  - mania_pipeline/scripts/03_lgbm_train.py
key_decisions:
  - Default profile remains baseline to preserve backward-compatible behavior.
patterns_established:
  - Profile-resolved parameter map instead of inline static params.
observability_surfaces:
  - train payload: `training_profile`, `training_params`
duration: ~25m
verification_result: passed
completed_at: 2026-03-15
blocker_discovered: false
---

# T01: Add named training profiles to baseline trainer

**Trainer now supports named profiles and persists profile metadata in payload.**

## What Happened

- Added `TRAINING_PROFILES` map with `baseline` and `quality_v1`.
- Added `resolve_training_params(profile, random_state)` helper with fail-fast unknown profile handling.
- Extended `train_baseline(..., profile=...)` and persisted `training_profile` + `training_params` in payload.

## Verification

- Covered via `test_run_pipeline_m003_s01_training_profile_contract.py` profile checks ✅

## Diagnostics

- Runtime prints selected training profile and metadata persists it in train payload.

## Deviations

none

## Known Issues

- `quality_v1` is seed profile, not HPO-optimized yet.

## Files Created/Modified

- `mania_pipeline/scripts/03_lgbm_train.py` — profile-aware trainer implementation.
