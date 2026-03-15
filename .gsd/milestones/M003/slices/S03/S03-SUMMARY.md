---
id: S03
parent: M003
milestone: M003
provides:
  - Ensemble candidate integration surface in canonical eval stage.
requires:
  - slice: S02
    provides: deterministic HPO report contract
affects:
  - S04
key_files:
  - mania_pipeline/scripts/run_pipeline.py
  - mania_pipeline/tests/test_run_pipeline_m003_s03_ensemble_contract.py
key_decisions:
  - Ensemble selection remains deterministic and baseline-guarded by minimum Val-Brier improvement.
patterns_established:
  - Eval-stage candidate ledger pattern (`baseline`, `hpo_best`, `ensemble_weighted`) with reason-coded status.
observability_surfaces:
  - ensemble_report.json
  - run_metadata.json.stage_outputs.eval_report.ensemble
drill_down_paths:
  - .gsd/milestones/M003/slices/S03/tasks/T01-SUMMARY.md
  - .gsd/milestones/M003/slices/S03/tasks/T02-SUMMARY.md
  - .gsd/milestones/M003/slices/S03/tasks/T03-SUMMARY.md
duration: ~1h35m
verification_result: passed
completed_at: 2026-03-15
---

# S03: Ensemble Candidate Integration

**Canonical eval stage now emits baseline-vs-HPO-vs-blend candidate comparison with deterministic selection signal and artifact contract wiring.**

## What Happened

S03 added ensemble decisioning as an eval-stage extension (no topology change):
- Introduced deterministic candidate scoring for `baseline`, `hpo_best`, and `ensemble_weighted`.
- Consumed S02 `hpo_report.json` best overrides to retrain HPO candidate during eval.
- Added threshold-guarded selection logic against baseline (`ENSEMBLE_MIN_VAL_IMPROVEMENT`).
- Persisted `ensemble_report.json` and mirrored summary under `stage_outputs.eval_report.ensemble`.
- Extended artifact contract required set with `ensemble_report_json`.

Integration tests and canonical runtime smoke confirmed end-to-end wiring.

## Verification

- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_m003_s03_ensemble_contract.py mania_pipeline/tests/test_run_pipeline_s03_eval_contract.py mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py mania_pipeline/tests/test_run_pipeline_s07_submission_contract.py mania_pipeline/tests/test_run_pipeline_m002_s04_policy_gate_contract.py mania_pipeline/tests/test_run_pipeline_m003_s02_hpo_contract.py -q` ✅
- `./venv/Scripts/python -m pytest mania_pipeline/tests -q` ✅ (52 passed)
- `./venv/Scripts/python mania_pipeline/scripts/run_pipeline.py --seed 42 --training-profile quality_v1 --hpo-trials 2 --hpo-target-profile quality_v1 --run-label m003_s03_ensemble_smoke --artifacts-root mania_pipeline/artifacts/runs_m003` ✅
- post-run assert: ensemble report + metadata mirror + aggregate decision ✅

## Requirements Advanced

- R015 — Ensemble capability baseline train/eval contracts üzerine bağlandı.

## Requirements Validated

- R015 — S03 ensemble report contract testi + canonical smoke proof ile doğrulandı.

## New Requirements Surfaced

- none

## Requirements Invalidated or Re-scoped

- none

## Deviations

none

## Known Limitations

- Ensemble stratejisi şu an tek blend ailesi (baseline + hpo_best weighted blend); stacked/metalearner henüz yok.

## Follow-ups

- S04’te submission readiness gate, `ensemble.aggregate.decision` sinyalini release kararına dahil etmeli.

## Files Created/Modified

- `mania_pipeline/scripts/run_pipeline.py` — ensemble scoring, report wiring, artifact contract update.
- `mania_pipeline/tests/test_run_pipeline_m003_s03_ensemble_contract.py` — S03 contract test.
- `mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py` — fixture update for new required artifact.
- `mania_pipeline/tests/test_run_pipeline_s07_submission_contract.py` — fixture update for new required artifact.
- `mania_pipeline/tests/test_run_pipeline_m002_s04_policy_gate_contract.py` — fixture update for new required artifact.

## Forward Intelligence

### What the next slice should know
- S04 readiness logic artık ensemble decision surface’ini doğrudan tüketebilir (`stage_outputs.eval_report.ensemble.aggregate`).

### What's fragile
- HPO retrain candidate başarısız olduğunda blend path otomatik düşüyor; readiness kararında bu ayrımı reason-coded değerlendirmek önemli.

### Authoritative diagnostics
- İlk bakılacak yer: `ensemble_report.json` (candidate ledger + selection reason), ardından metadata mirror.

### What assumptions changed
- Ensemble için ayrı stage gerekmedi; eval-stage extension mevcut topology içinde yeterli oldu.
