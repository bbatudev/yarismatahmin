---
id: S02
parent: M003
milestone: M003
provides:
  - Reproducible HPO trial harness with train-stage report contract.
requires:
  - slice: S01
    provides: training profile seam
affects:
  - S03
key_files:
  - mania_pipeline/scripts/run_pipeline.py
  - mania_pipeline/scripts/03_lgbm_train.py
  - mania_pipeline/tests/test_run_pipeline_m003_s02_hpo_contract.py
key_decisions:
  - HPO harness is optional and deterministic; report is always emitted (skipped/passed/failed).
patterns_established:
  - Train-stage optimization workflows persist candidate-level diagnostics as first-class artifacts.
observability_surfaces:
  - hpo_report.json
  - run_metadata.json.stage_outputs.train.hpo
drill_down_paths:
  - .gsd/milestones/M003/slices/S02/tasks/T01-SUMMARY.md
  - .gsd/milestones/M003/slices/S02/tasks/T02-SUMMARY.md
  - .gsd/milestones/M003/slices/S02/tasks/T03-SUMMARY.md
duration: ~1h20m
verification_result: passed
completed_at: 2026-03-15
---

# S02: Reproducible HPO Search Harness

**Canonical train stage now supports deterministic HPO trial search with machine-readable candidate and winner diagnostics.**

## What Happened

S02 introduced HPO as a controlled train-stage harness:
- Deterministic trial parameter generator added (seed-bound).
- Train invocation wrapper now supports profile + param overrides while preserving backward compatibility.
- `--hpo-trials` and `--hpo-target-profile` CLI flags added.
- Train stage emits `hpo_report.json` and mirrors summary under `stage_outputs.train.hpo`.
- Report is always present with explicit status (`skipped|passed|failed`).

This sets the optimization substrate for S03 ensemble decisions without changing canonical stage topology.

## Verification

- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_m003_s02_hpo_contract.py mania_pipeline/tests/test_run_pipeline_m003_s01_training_profile_contract.py mania_pipeline/tests/test_run_pipeline_cli.py mania_pipeline/tests/test_run_pipeline_s03_eval_contract.py -q` ✅
- `./venv/Scripts/python -m pytest mania_pipeline/tests -q` ✅ (51 passed)
- `./venv/Scripts/python mania_pipeline/scripts/run_pipeline.py --seed 42 --training-profile quality_v1 --hpo-trials 2 --hpo-target-profile quality_v1 --run-label m003_s02_hpo_smoke --artifacts-root mania_pipeline/artifacts/runs_m003` ✅
- post-run HPO report/payload assert ✅

## Requirements Advanced

- R013 — HPO search capability train-stage contract olarak canonical run’a bağlandı.

## Requirements Validated

- R013 — deterministic HPO trial report contract test + runtime smoke proof ile doğrulandı.

## New Requirements Surfaced

- none

## Requirements Invalidated or Re-scoped

- none

## Deviations

none

## Known Limitations

- Search strategy simple deterministic trial sampling; Optuna sampler-level optimization henüz yok.

## Follow-ups

- S03’te HPO winner sinyallerini ensemble candidate seçiminde tüket.
- Gerekirse S03/S04’te trial budget ve search space tuning yap.

## Files Created/Modified

- `mania_pipeline/scripts/run_pipeline.py` — HPO harness + report wiring + CLI args.
- `mania_pipeline/scripts/03_lgbm_train.py` — param override support.
- `mania_pipeline/tests/test_run_pipeline_m003_s02_hpo_contract.py` — S02 contract tests.
- `.gsd/milestones/M003/slices/S02/S02-PLAN.md` — completed tasks.

## Forward Intelligence

### What the next slice should know
- HPO output already provides per-gender best trial signal and candidate ledger ready for ensemble selection.

### What's fragile
- `hpo_trials` increases runtime linearly; high values can inflate canonical run duration quickly.

### Authoritative diagnostics
- First stop: `run_metadata.json.stage_outputs.train.hpo`, then `hpo_report.json`.

### What assumptions changed
- HPO did not need a separate pipeline stage; train-stage extension is sufficient for current milestone.
