---
estimated_steps: 4
estimated_files: 3
---

# T03: Runtime proof and S01 closure

**Slice:** S01 — Training Profile Contract (Baseline vs Quality v1)
**Milestone:** M003

## Description

Quality profile ile gerçek canonical run alır, metadata propagation’ı doğrular ve S01 dokümanlarını kapatır.

## Steps

1. `quality_v1` profile smoke run çalıştır.
2. Metadata assert ile profile propagation kontrol et.
3. T03 task summary yaz.
4. S01 slice summary ve roadmap/state güncellemelerini yap.

## Must-Haves

- [ ] `stage_outputs.train.training_profile == quality_v1`
- [ ] Men/Women payload’larında profile alanı görünür.

## Verification

- `./venv/Scripts/python mania_pipeline/scripts/run_pipeline.py --seed 42 --training-profile quality_v1 --run-label m003_s01_profile_smoke`

## Inputs

- `mania_pipeline/artifacts/runs/<run_id>/run_metadata.json`

## Expected Output

- `.gsd/milestones/M003/slices/S01/tasks/T03-SUMMARY.md`
- `.gsd/milestones/M003/slices/S01/S01-SUMMARY.md`
