---
estimated_steps: 4
estimated_files: 3
---

# T03: Runtime proof and closure artifacts

**Slice:** S03 — Ensemble Candidate Integration
**Milestone:** M003

## Description

HPO-enabled canonical run ile ensemble report ve metadata mirror kontratını doğrular; S03 closure dokümanlarını tamamlar.

## Steps

1. S03 smoke run çalıştır.
2. `ensemble_report.json` varlığını assert et.
3. metadata `stage_outputs.eval_report.ensemble` mirror’ını assert et.
4. Task/slice summary dosyalarını yaz.

## Must-Haves

- [x] Runtime’da aggregate ensemble decision üretilir.
- [x] Smoke proof path dokümante edilir.

## Verification

- `./venv/Scripts/python mania_pipeline/scripts/run_pipeline.py --seed 42 --training-profile quality_v1 --hpo-trials 2 --hpo-target-profile quality_v1 --run-label m003_s03_ensemble_smoke --artifacts-root mania_pipeline/artifacts/runs_m003`

## Inputs

- `mania_pipeline/artifacts/runs_m003/<run_id>/run_metadata.json`

## Expected Output

- `.gsd/milestones/M003/slices/S03/tasks/T03-SUMMARY.md`
- `.gsd/milestones/M003/slices/S03/S03-SUMMARY.md`
