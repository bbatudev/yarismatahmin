---
estimated_steps: 4
estimated_files: 2
---

# T03: Runtime smoke + comparison refresh

**Slice:** S03 — Ensemble Robustness Rules
**Milestone:** M004

## Verification

- `./venv/Scripts/python mania_pipeline/scripts/run_pipeline.py --seed 42 --training-profile quality_v1 --hpo-trials 2 --hpo-target-profile quality_v1 --submission-stage none --run-label m004_s03_ensemble_smoke --artifacts-root mania_pipeline/artifacts/runs_m004`
- `./venv/Scripts/python mania_pipeline/scripts/compare_run_metrics.py ...`
