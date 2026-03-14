---
id: S02
parent: M002
milestone: M002
provides:
  - Regime-aware calibration method selection contract with required artifact and eval payload wiring.
requires:
  - slice: S01
    provides: drift regime signal payload and report surface.
affects:
  - S03
  - S04
key_files:
  - mania_pipeline/scripts/run_pipeline.py
  - mania_pipeline/tests/test_run_pipeline_m002_s02_calibration_policy_contract.py
  - mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py
  - mania_pipeline/tests/test_run_pipeline_s07_submission_contract.py
key_decisions:
  - Calibration selection is Val-Brier driven with regime-aware default fallback and reason-coded candidate availability.
patterns_established:
  - Eval-stage sub-report (`calibration_policy_report.json`) mirrored into `stage_outputs.eval_report` and enforced in artifact contract.
observability_surfaces:
  - calibration_policy_report.json
  - eval_report.json.calibration_policy
  - run_metadata.json.stage_outputs.eval_report.calibration_policy
drill_down_paths:
  - .gsd/milestones/M002/slices/S02/tasks/T01-SUMMARY.md
  - .gsd/milestones/M002/slices/S02/tasks/T02-SUMMARY.md
  - .gsd/milestones/M002/slices/S02/tasks/T03-SUMMARY.md
duration: ~1h25m
verification_result: passed
completed_at: 2026-03-15
---

# S02: Regime-Aware Calibration Policy Engine

**Canonical eval flow now emits deterministic regime-aware calibration policy decisions as first-class contract artifacts.**

## What Happened

S02 added calibration policy as a canonical layer without changing stage topology:
- Candidate methods (`none`, `platt`, `isotonic`) are evaluated with consistent Val/Test metric bundles.
- Availability guardrails (minimum Val sample, single-class Val) produce explicit `status/reason` payloads instead of silent behavior.
- Drift-driven regime context determines method order/default, while Val-Brier remains the optimization objective.
- Policy outputs are persisted to `calibration_policy_report.json` and mirrored into eval output payload.

Artifact-stage required contract list was expanded with `calibration_policy_report_json`, and fixture-based S06/S07 tests were aligned to prevent contract drift.

## Verification

- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_m002_s02_calibration_policy_contract.py mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py mania_pipeline/tests/test_run_pipeline_s07_submission_contract.py -q` ✅
- `./venv/Scripts/python -m pytest mania_pipeline/tests -q` ✅
- `./venv/Scripts/python mania_pipeline/scripts/run_pipeline.py --seed 42 --run-label m002_s02_policy_smoke` ✅
- post-run policy artifact/payload assert ✅

## Requirements Advanced

- R014 — Rejim-bazlı calibration selection policy contract’ı canonical runtime’da üretildi.

## Requirements Validated

- R014 — `calibration_policy_report.json` + metadata mirror + full-suite+smoke proof ile runtime doğrulandı.

## New Requirements Surfaced

- none

## Requirements Invalidated or Re-scoped

- none

## Deviations

none

## Known Limitations

- Regime/order ve improvement thresholds statik başlangıç değerleri; adaptif tuning yapılmadı.
- Policy henüz governance decision fusion’a bağlanmadı (S03 scope).

## Follow-ups

- S03’te policy çıktısını governance decision evidence bundle’a bağla.
- S04’te regression gate davranışını policy sinyaliyle birlikte final integration proof’a taşı.

## Files Created/Modified

- `mania_pipeline/scripts/run_pipeline.py` — policy helpers, report emission, artifact required surface updates.
- `mania_pipeline/tests/test_run_pipeline_m002_s02_calibration_policy_contract.py` — S02 contract tests.
- `mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py` — fixture alignment.
- `mania_pipeline/tests/test_run_pipeline_s07_submission_contract.py` — fixture alignment.
- `.gsd/milestones/M002/slices/S02/S02-PLAN.md` — completed task tracking.

## Forward Intelligence

### What the next slice should know
- `calibration_policy.by_gender` içinde candidate metrics + selection reason hazır; S03 doğrudan consume edebilir.

### What's fragile
- `min_improvement` düşük tutulduğunda method switching daha sık olabilir; governance coupling’de churn riski var.

### Authoritative diagnostics
- İlk bakış noktası: `run_metadata.json.stage_outputs.eval_report.calibration_policy`.

### What assumptions changed
- Policy motoru için yeni stage gerekmedi; eval-stage extension yeterli kaldı.
