# Handoff - 2026-03-19 Final Prep

## Current Phase

- Research phase is effectively closed.
- Current phase is release / Kaggle packaging / final submission prep.
- Core remaining issue is not model discovery; it is final recipe activation plus calibration gate.

## What Was Completed

### M005 Research Summary

- Evaluation discipline added:
  - multi-season weighted gate
  - error decomposition
  - calibration / drift / governance reporting
- Feature branch explored:
  - PythWR
  - Luck
  - men-only elite Massey spread / disagreement
  - seed mispricing
  - style clash
- Alternative model families explored:
  - HistGB
  - logistic regression
  - spline-logistic GAM-like
  - XGBoost
  - CatBoost
  - TabPFN
- Additional policy branches explored:
  - stacking / meta-policy
  - men external-prior / disagreement policy
  - men combo follow-up
  - men residual correction
  - men regime routing
  - men gate-aware search

### Strategic Outcome

- Women produced strong non-baseline candidates.
- Men produced promising raw signals, but no clean canonical promotion.
- Men discipline-safe line converged around:
  - `0.5 LGBM + 0.5 HistGB`

## Important Commits Already Pushed

- `fec4d73` - `Finalize M005 research and prep for Kaggle packaging`
- `7926c71` - `docs: update README for M005 status and release phase`

## Current Shipping Intent

Initial release intent was:

- `training_profile = quality_v1`
- `prediction_policy = blend_final_recipe_v1`
- `submission_stage = stage2`

But this has not yet been validated end-to-end because the explicit final recipe still falls back incorrectly.

## Final Dry-Run History

### v1

Run:
- `20260318T224827Z_final_recipe_dry_run`

Outcome:
- Requested `blend_candidate_v1`
- Actually fell back to baseline / mixed baseline fallback
- Blocked by calibration gate

### v2

Run:
- `20260318T233309Z_final_recipe_dry_run_v2`

Outcome:
- Explicit static final recipe activated correctly
- Men:
  - `0.5 baseline + 0.5 histgb`
- Women:
  - `0.6 baseline + 0.4 histgb`
- Brier improved for both genders
- Still blocked by:
  - `men:calibration_degraded`
  - `women:calibration_degraded`

Key metrics:
- men test brier: `0.17889898260668147`
- women test brier: `0.1335608356930658`

### v3 / v4 / v5

Goal:
- Replace static explicit recipe with selected dynamic candidates from `alternative_model_report`

Expected selected candidates:
- men:
  - `baseline_histgb_spline_logistic_blend`
  - weights `{baseline: 0.5, histgb_benchmark: 0.25, spline_logistic_benchmark: 0.25}`
- women:
  - `spline_logistic_tabpfn_blend`
  - weights `{spline_logistic_benchmark: 0.75, tabpfn_benchmark: 0.25}`

But actual outcome in v3 / v4 / v5:
- `blend_final_recipe_v1` still fell back to baseline
- `prediction_policy.selected_policy` ended up as:
  - `mixed_with_baseline_fallback`
- by gender:
  - men -> baseline
  - women -> baseline

Latest run:
- `20260319T003117Z_final_recipe_dry_run_v5`

Latest blocker:
- `men:calibration_degraded`
- `women:calibration_degraded`

Reason:
- final explicit recipe plumbing still does not consume dynamic alternative-model selections correctly at runtime

## Files Most Relevant Right Now

- `/Users/gokturkcan/Desktop/ML_March_Mania2026_NCAA/mania_pipeline/scripts/run_pipeline.py`
- `/Users/gokturkcan/Desktop/ML_March_Mania2026_NCAA/.gsd/FINAL-RECIPE.md`
- `/Users/gokturkcan/Desktop/ML_March_Mania2026_NCAA/mania_pipeline/tests/test_run_pipeline_m005_s05_alternative_model_contract.py`
- `/Users/gokturkcan/Desktop/ML_March_Mania2026_NCAA/mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py`

## Latest Relevant Artifacts

### Latest full run

- `/Users/gokturkcan/Desktop/ML_March_Mania2026_NCAA/mania_pipeline/artifacts/runs/20260319T003117Z_final_recipe_dry_run_v5/`

Most relevant files inside:
- `eval_report.json`
- `alternative_model_report.json`
- `final_blend_recipe_report.json`
- `regression_gate_report.json`
- `submission_readiness_report.json`
- `stage_events.jsonl`

### Best static explicit recipe run

- `/Users/gokturkcan/Desktop/ML_March_Mania2026_NCAA/mania_pipeline/artifacts/runs/20260318T233309Z_final_recipe_dry_run_v2/`

This is useful because:
- explicit recipe really activated there
- calibration blocker was measured cleanly there

## Current Diagnosis

There are two separate issues:

1. Explicit dynamic final recipe still falls back incorrectly
- selection in `alternative_model_report.json` is correct
- but `blend_final_recipe_v1` runtime path still does not apply it

2. Even when explicit static blend recipe activates, calibration gate still blocks
- so after plumbing is fixed, calibration may still need a final decision

## Recommended Next Step

Do not reopen broad research.

Instead:

1. Fix `blend_final_recipe_v1` so it actually uses dynamic selected weights from `alternative_model_report`
2. Re-run one final dry-run
3. If calibration still blocks:
   - decide whether to ship a more conservative recipe
   - or explicitly relax / reframe final submission policy outside canonical artifact gate
4. Then move to:
   - Kaggle packaging
   - Kaggle smoke
   - final submit

## Key Truth To Preserve

- The current problem is no longer model discovery.
- The current problem is release plumbing and final operational policy.
