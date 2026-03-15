# S04: Final Performance Proof + Freeze

**Goal:** Final önce/sonra performans kanıtını üretmek ve readiness+submission smoke ile freeze kararını netlemek.
**Demo:** `S04-FINAL-COMPARISON.json` + final run readiness/submission kanıtı mevcut.

## Verification

- `./venv/Scripts/python mania_pipeline/scripts/run_pipeline.py --seed 42 --training-profile quality_v1 --hpo-trials 2 --hpo-target-profile quality_v1 --submission-stage stage2 --run-label m004_s04_final_freeze --artifacts-root mania_pipeline/artifacts/runs_m004`
- `./venv/Scripts/python mania_pipeline/scripts/compare_run_metrics.py --baseline-run mania_pipeline/artifacts/runs_m003/s04_gate/20260314T233640Z_m003_s04_readiness_gate --candidate-run mania_pipeline/artifacts/runs_m004/20260315T001052Z_m004_s04_final_freeze --output-json .gsd/milestones/M004/S04-FINAL-COMPARISON.json`

## Tasks

- [x] **T01: Final readiness+submission smoke run** `est:30m`
- [x] **T02: Final baseline comparison artifact** `est:10m`
- [x] **T03: Freeze decision + closure docs** `est:20m`
