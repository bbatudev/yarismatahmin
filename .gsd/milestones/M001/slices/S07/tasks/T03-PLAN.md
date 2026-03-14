---
estimated_steps: 4
estimated_files: 5
---

# T03: Prove final integration runtime with submission enabled and update milestone state

**Slice:** S07 — Optional Submission Validation + Final Integration
**Milestone:** M001

## Description

Submission-enabled canonical smoke run alınır, contract assert’leri geçilir ve milestone closure dokümanları güncellenir.

## Steps

1. Submission-enabled smoke run çalıştır.
2. `run_metadata` + submission artifact/report assert’lerini çalıştır.
3. Requirement/roadmap/project/state dosyalarında M001 kapanışını güncelle.
4. Slice summary ile final integration proof’u kaydet.

## Must-Haves

- [x] Runtime’da submission contract pass verir.
- [x] M001’de aktif requirement kalmaz.

## Verification

- `./venv/Scripts/python mania_pipeline/scripts/run_pipeline.py --seed 42 --run-label s07_submission_smoke --submission-stage stage2`
- `./venv/Scripts/python -m pytest mania_pipeline/tests -q`

## Inputs

- `.gsd/REQUIREMENTS.md` — R012 closure target
- `.gsd/milestones/M001/M001-ROADMAP.md` — S07 completion state

## Expected Output

- `.gsd/milestones/M001/slices/S07/S07-SUMMARY.md` — final assembly proof
- `.gsd/REQUIREMENTS.md` — R012 validated
- `.gsd/milestones/M001/M001-ROADMAP.md` — S07 marked complete
