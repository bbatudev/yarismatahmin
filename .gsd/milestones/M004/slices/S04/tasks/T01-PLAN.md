---
estimated_steps: 3
estimated_files: 1
---

# T01: Final readiness+submission smoke

**Slice:** S04 — Final Performance Proof + Freeze
**Milestone:** M004

## Verification

- `./venv/Scripts/python mania_pipeline/scripts/run_pipeline.py --seed 42 --training-profile quality_v1 --hpo-trials 2 --hpo-target-profile quality_v1 --submission-stage stage2 --run-label m004_s04_final_freeze --artifacts-root mania_pipeline/artifacts/runs_m004`
