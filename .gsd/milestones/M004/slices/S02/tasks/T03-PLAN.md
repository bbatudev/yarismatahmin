---
estimated_steps: 4
estimated_files: 2
---

# T03: Contract test + smoke proof

**Slice:** S02 — CV-Strengthened HPO Selection
**Milestone:** M004

## Verification

- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_m004_s02_hpo_cv_contract.py -q`
- `./venv/Scripts/python mania_pipeline/scripts/run_pipeline.py --seed 42 --training-profile quality_v1 --hpo-trials 2 --hpo-target-profile quality_v1 --submission-stage none --run-label m004_s02_hpo_cv_smoke --artifacts-root mania_pipeline/artifacts/runs_m004`
