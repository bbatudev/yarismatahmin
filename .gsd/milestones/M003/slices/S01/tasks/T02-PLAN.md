---
estimated_steps: 5
estimated_files: 2
---

# T02: Orchestrator profile wiring

**Slice:** S01 — Training Profile Contract (Baseline vs Quality v1)
**Milestone:** M003

## Description

CLI/context/train stage arasında training-profile bilgisini geçirir ve metadata’da görünür kılar.

## Steps

1. CLI’ye `--training-profile` ekle.
2. Context’e profile alanını ekle.
3. `stage_train` çağrısında profile’ı `train_baseline` fonksiyonuna geçir.
4. Train payload’a top-level `training_profile` ekle.
5. Contract testlerle doğrula.

## Must-Haves

- [ ] Profile bilgisi `stage_outputs.train` altında persist edilir.
- [ ] Default run’da profile baseline kalır.

## Verification

- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_m003_s01_training_profile_contract.py -q`

## Inputs

- `mania_pipeline/scripts/run_pipeline.py` — CLI/context/stage train wiring.
- `mania_pipeline/scripts/03_lgbm_train.py` — profile-aware trainer.

## Expected Output

- `mania_pipeline/scripts/run_pipeline.py` — profile wiring.
- `mania_pipeline/tests/test_run_pipeline_m003_s01_training_profile_contract.py` — orchestration contract checks.
