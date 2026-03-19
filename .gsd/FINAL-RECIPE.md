# Final Recipe

## Current Shipping Recommendation

The current production-safe recipe is the policy path that is already wired into the canonical submission pipeline:

- `prediction_policy = blend_candidate_v1`
- `training_profile = quality_v1`
- `submission_stage = stage2`

## Why This Recipe

- It is already implemented in the canonical `run_pipeline.py` selection path.
- It uses the strongest discipline-safe men candidate currently available in production form:
  - men: `0.5 * LGBM + 0.5 * HistGB`
- It also preserves the best currently productized women-side candidate:
  - women: blend-candidate policy path from `blend_candidate_policy_report.json`

## Important Constraint

Women-side research later produced stronger candidates (`TabPFN`, `spline_logistic`, and blend variants), but they are still research artifacts, not the active submission policy. Therefore they are not part of the current shipping recipe.

## Finalization Sequence

1. Run a local final dry-run with the shipping recipe.
2. Verify artifact outputs and submission schema.
3. Prepare Kaggle-format packaging.
4. Run a Kaggle smoke.
5. Submit.
