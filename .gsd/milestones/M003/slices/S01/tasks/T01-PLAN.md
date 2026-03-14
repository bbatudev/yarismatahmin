---
estimated_steps: 5
estimated_files: 1
---

# T01: Named training profiles in trainer

**Slice:** S01 — Training Profile Contract (Baseline vs Quality v1)
**Milestone:** M003

## Description

Baseline trainer içine profile tabanlı param çözümleme ekler ve payload’a profile metadata yazar.

## Steps

1. Profile map (`baseline`, `quality_v1`) tanımla.
2. Param resolver helper ekle.
3. `train_baseline` imzasına `profile` argümanı ekle.
4. Unknown profile için fail-fast hata döndür.
5. Payload’a `training_profile` ve `training_params` yaz.

## Must-Haves

- [ ] Default profile baseline davranışını korur.
- [ ] Profile seçimi deterministic olur.

## Verification

- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_m003_s01_training_profile_contract.py -k "profiles" -q`

## Inputs

- `mania_pipeline/scripts/03_lgbm_train.py` — mevcut sabit params trainer.

## Expected Output

- `mania_pipeline/scripts/03_lgbm_train.py` — profile-aware trainer.
