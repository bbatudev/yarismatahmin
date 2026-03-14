---
id: T01
parent: S02
milestone: M003
provides:
  - Deterministic HPO trial generator and compatible train invocation wrapper.
key_files:
  - mania_pipeline/scripts/run_pipeline.py
  - mania_pipeline/scripts/03_lgbm_train.py
key_decisions:
  - HPO harness remains optional (`hpo_trials=0` => skipped) to preserve default runtime cost.
patterns_established:
  - Seed-based trial param generation with per-trial status records.
observability_surfaces:
  - hpo candidate `status/reason/metrics` rows
duration: ~35m
verification_result: passed
completed_at: 2026-03-15
blocker_discovered: false
---

# T01: Add HPO trial generation and train invocation compatibility

**Implemented deterministic HPO trial engine and profile/override-compatible train calling.**

## What Happened

- Added deterministic HPO param search space and trial generation helpers.
- Added robust train invocation wrapper supporting both new kwargs (`profile`, `param_overrides`) and legacy stubs.
- Extended trainer param resolver to accept optional overrides.

## Verification

- Covered by `test_run_pipeline_m003_s02_hpo_contract.py` deterministic checks ✅

## Diagnostics

- Per-trial failure reasons are persisted under candidate rows.

## Deviations

none

## Known Issues

- Search space is currently bounded manual grid; Optuna sampler not yet integrated.

## Files Created/Modified

- `mania_pipeline/scripts/run_pipeline.py` — trial engine and wrapper.
- `mania_pipeline/scripts/03_lgbm_train.py` — param override support.
