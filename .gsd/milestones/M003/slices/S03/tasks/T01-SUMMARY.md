---
id: T01
parent: S03
milestone: M003
provides:
  - Deterministic ensemble candidate scoring and selection seam in eval stage.
key_files:
  - mania_pipeline/scripts/run_pipeline.py
key_decisions:
  - Ensemble selection remains threshold-gated against baseline to avoid noisy promotions.
patterns_established:
  - Candidate ledger (`baseline`, `hpo_best`, `ensemble_weighted`) with reason-coded status entries.
observability_surfaces:
  - ensemble_report.json.by_gender.<gender>.candidates
duration: ~45m
verification_result: passed
completed_at: 2026-03-15
blocker_discovered: false
---

# T01: Deterministic ensemble candidate scoring in eval stage

**Added eval-stage ensemble candidate scoring with deterministic selection and threshold guardrail.**

## What Happened

- Added ensemble constants (`ENSEMBLE_WEIGHT_GRID`, `ENSEMBLE_MIN_VAL_IMPROVEMENT`).
- Added helper seams for split-prob scoring and model-based Val/Test probability generation.
- Added per-gender candidate evaluation over `baseline`, `hpo_best`, `ensemble_weighted`.
- Added deterministic selection logic (best Val Brier + minimum improvement vs baseline).

## Verification

- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_m003_s03_ensemble_contract.py -q` ✅

## Diagnostics

- Candidate-level failures are explicit in `reason` (`hpo_retrain_failed`, `probability_shape_mismatch`, etc.).

## Deviations

none

## Known Issues

none

## Files Created/Modified

- `mania_pipeline/scripts/run_pipeline.py` — ensemble helpers and scoring integration.
