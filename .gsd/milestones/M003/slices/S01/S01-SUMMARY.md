---
id: S01
parent: M003
milestone: M003
provides:
  - Canonical training profile contract (`baseline|quality_v1`) with runtime metadata visibility.
requires:
  - slice: S04
    provides: policy-gated stable canonical runtime foundation
affects:
  - S02
key_files:
  - mania_pipeline/scripts/03_lgbm_train.py
  - mania_pipeline/scripts/run_pipeline.py
  - mania_pipeline/tests/test_run_pipeline_m003_s01_training_profile_contract.py
key_decisions:
  - Training profile selection is explicit CLI input and defaults to baseline.
patterns_established:
  - Profile-based trainer configuration + payload persistence as prerequisite seam for HPO.
observability_surfaces:
  - run_metadata.json.stage_outputs.train.training_profile
  - run_metadata.json.stage_outputs.train.genders.<gender>.training_profile
drill_down_paths:
  - .gsd/milestones/M003/slices/S01/tasks/T01-SUMMARY.md
  - .gsd/milestones/M003/slices/S01/tasks/T02-SUMMARY.md
  - .gsd/milestones/M003/slices/S01/tasks/T03-SUMMARY.md
duration: ~1h15m
verification_result: passed
completed_at: 2026-03-15
---

# S01: Training Profile Contract (Baseline vs Quality v1)

**Canonical train stage now supports explicit training profiles and persists profile identity in runtime artifacts.**

## What Happened

S01 delivered the first model-evolution seam for M003 without breaking existing topology:
- Trainer moved from hardcoded params to named profile map (`baseline`, `quality_v1`).
- Orchestrator accepts `--training-profile` and forwards it to train stage.
- Train payload now persists profile identity and selected params per gender.
- Backward compatibility was preserved for legacy test stubs that do not yet accept `profile` argument.

This creates a controlled path to change model behavior in later slices (HPO/ensemble) while keeping execution deterministic and observable.

## Verification

- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_m003_s01_training_profile_contract.py -q` ✅
- `./venv/Scripts/python -m pytest mania_pipeline/tests -q` ✅ (49 passed)
- `./venv/Scripts/python mania_pipeline/scripts/run_pipeline.py --seed 42 --training-profile quality_v1 --run-label m003_s01_profile_smoke --artifacts-root mania_pipeline/artifacts/runs_m003` ✅
- post-run metadata profile assert ✅

## Requirements Advanced

- R013 — HPO öncesi profile-contract seam oluşturularak tuning altyapısı hazırlandı.

## Requirements Validated

- none

## New Requirements Surfaced

- none

## Requirements Invalidated or Re-scoped

- none

## Deviations

none

## Known Limitations

- `quality_v1` profile başlangıç konfigürasyonu; sistematik search ile optimize edilmedi.

## Follow-ups

- S02’de reproducible HPO harness ve `hpo_report.json` eklenmeli.
- Profile performans karşılaştırması gate policy ile bağlanmalı.

## Files Created/Modified

- `mania_pipeline/scripts/03_lgbm_train.py` — profile-aware trainer.
- `mania_pipeline/scripts/run_pipeline.py` — CLI/context/train profile wiring.
- `mania_pipeline/tests/test_run_pipeline_m003_s01_training_profile_contract.py` — S01 contract tests.
- `.gsd/milestones/M003/slices/S01/S01-PLAN.md` — task completion state.

## Forward Intelligence

### What the next slice should know
- Profile contract artık stable; S02 doğrudan profile candidates üreterek HPO raporlayabilir.

### What's fragile
- `quality_v1` bazen existing historical baselines karşısında regression gate bloklayabilir; isolated artifacts-root proof yaklaşımı gerekebilir.

### Authoritative diagnostics
- İlk kontrol: `run_metadata.json.stage_outputs.train.training_profile`.

### What assumptions changed
- Model değişikliği için doğrudan HPO’ya atlamak yerine önce profile seam kurmak daha güvenli çıktı.
