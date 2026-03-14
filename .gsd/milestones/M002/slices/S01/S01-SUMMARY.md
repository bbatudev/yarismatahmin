---
id: S01
parent: M002
milestone: M002
provides:
  - Canonical drift/regime baseline artifact and eval payload contract for Men/Women.
requires:
  - slice: S07
    provides: stable artifact-stage enforcement and canonical runtime proof discipline.
affects:
  - S02
key_files:
  - mania_pipeline/scripts/run_pipeline.py
  - mania_pipeline/tests/test_run_pipeline_m002_s01_drift_contract.py
  - mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py
  - mania_pipeline/tests/test_run_pipeline_s07_submission_contract.py
key_decisions:
  - Drift segmentation uses deterministic `SeedNum_diff` bins (`close|medium|wide`) for first policy baseline.
patterns_established:
  - Drift diagnostics emitted as eval-stage artifact mirroring calibration/governance pattern.
observability_surfaces:
  - drift_regime_report.json
  - eval_report.json.drift
  - run_metadata.json.stage_outputs.eval_report.drift
drill_down_paths:
  - .gsd/milestones/M002/slices/S01/tasks/T01-SUMMARY.md
  - .gsd/milestones/M002/slices/S01/tasks/T02-SUMMARY.md
  - .gsd/milestones/M002/slices/S01/tasks/T03-SUMMARY.md
duration: ~1h20m
verification_result: passed
completed_at: 2026-03-15
---

# S01: Regime Drift Baseline & Signal Contract

**Canonical eval flow now emits deterministic drift regime diagnostics as a first-class artifact and payload surface.**

## What Happened

S01 introduced drift as a canonical quality signal without adding a new stage:
- Split-level drift summaries (`sample_count`, `pred_mean`, `actual_rate`, `gap`) are computed for each gender.
- Test split regime segmentation (`close|medium|wide`) is computed from `SeedNum_diff`.
- Reason-coded alerts (`test_gap_shift`, `low_sample_regime`, `seed_feature_missing`) are produced deterministically.
- Drift artifact (`drift_regime_report.json`) is emitted and mirrored into eval report + run metadata payloads.

Artifact-stage contract requirements were updated accordingly, and existing S06/S07 fixtures were aligned with the new required drift artifact surface.

## Verification

- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_m002_s01_drift_contract.py` ✅
- `./venv/Scripts/python -m pytest mania_pipeline/tests -q` ✅
- `./venv/Scripts/python mania_pipeline/scripts/run_pipeline.py --seed 42 --run-label m002_s01_drift_smoke` ✅
- post-run assertion for drift artifact/payload mirror ✅

## Requirements Advanced

- R014 — Rejim-bazlı calibration policy için gerekli drift observability yüzeyi oluşturuldu.

## Requirements Validated

- none

## New Requirements Surfaced

- none

## Requirements Invalidated or Re-scoped

- none

## Deviations

none

## Known Limitations

- Regime eşikleri başlangıç için sabit; adaptif/dinamik eşikler henüz yok.
- Smoke run’da alert üretimi eşik altı kaldı; policy coupling S02’de ele alınacak.

## Follow-ups

- S02’de drift sinyalini calibration method selector’a bağla.
- Alert eşiklerinin policy-level tuning stratejisini belirle.

## Files Created/Modified

- `mania_pipeline/scripts/run_pipeline.py` — drift helpers + artifact emission + payload wiring.
- `mania_pipeline/tests/test_run_pipeline_m002_s01_drift_contract.py` — drift contract tests.
- `mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py` — drift required-artifact fixture alignment.
- `mania_pipeline/tests/test_run_pipeline_s07_submission_contract.py` — drift required-artifact fixture alignment.
- `.gsd/milestones/M002/slices/S01/S01-PLAN.md` — S01 tasks marked complete.

## Forward Intelligence

### What the next slice should know
- Drift report already carries per-gender split/regime summaries, so S02 can consume directly without re-scoring.

### What's fragile
- Seed-based regimes are pragmatic but coarse; policy decisions should not overfit to one season snapshot.

### Authoritative diagnostics
- `run_metadata.json.stage_outputs.eval_report.drift` is the quickest control-plane surface; full detail is in `drift_regime_report.json`.

### What assumptions changed
- Drift observability required no new stage; eval-stage extension remained sufficient.
