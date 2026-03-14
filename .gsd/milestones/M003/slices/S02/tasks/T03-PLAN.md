---
estimated_steps: 4
estimated_files: 3
---

# T03: Runtime proof and S02 closure

**Slice:** S02 — Reproducible HPO Search Harness
**Milestone:** M003

## Description

HPO-enabled canonical run ile artifact/payload kanıtı alır ve S02 dokümantasyon kapanışını yapar.

## Steps

1. HPO smoke run çalıştır.
2. `hpo_report.json` varlığını ve metadata mirror’ı assert et.
3. T03 summary yaz.
4. S02 slice summary + roadmap/state güncelle.

## Must-Haves

- [ ] `hpo_report.json` runtime’da üretilmeli.
- [ ] `stage_outputs.train.hpo` metadata’da görünmeli.

## Verification

- `./venv/Scripts/python mania_pipeline/scripts/run_pipeline.py --seed 42 --training-profile quality_v1 --hpo-trials 2 --hpo-target-profile quality_v1 --run-label m003_s02_hpo_smoke --artifacts-root mania_pipeline/artifacts/runs_m003`

## Inputs

- `mania_pipeline/artifacts/runs_m003/<run_id>/run_metadata.json`

## Expected Output

- `.gsd/milestones/M003/slices/S02/tasks/T03-SUMMARY.md`
- `.gsd/milestones/M003/slices/S02/S02-SUMMARY.md`
