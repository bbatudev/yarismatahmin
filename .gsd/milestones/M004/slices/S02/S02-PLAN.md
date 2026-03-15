# S02: CV-Strengthened HPO Selection

**Goal:** HPO seçim sinyalini CV destekli objective ile daha stabil hale getirmek.
**Demo:** `hpo_report.json` candidate metrics içinde `objective_score` + `cv` detayları var ve seçim bu objective ile yapılıyor.

## Verification

- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_m003_s02_hpo_contract.py mania_pipeline/tests/test_run_pipeline_m004_s02_hpo_cv_contract.py -q`
- `./venv/Scripts/python -m pytest mania_pipeline/tests -q`
- `./venv/Scripts/python mania_pipeline/scripts/run_pipeline.py --seed 42 --training-profile quality_v1 --hpo-trials 2 --hpo-target-profile quality_v1 --submission-stage none --run-label m004_s02_hpo_cv_smoke --artifacts-root mania_pipeline/artifacts/runs_m004`

## Tasks

- [x] **T01: Add CV objective helper for HPO trials** `est:45m`
- [x] **T02: Wire objective score into candidate ranking/payload** `est:30m`
- [x] **T03: Add S02 CV contract test + runtime smoke proof** `est:30m`
