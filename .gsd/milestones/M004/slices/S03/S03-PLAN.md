# S03: Ensemble Robustness Rules

**Goal:** Ensemble candidate promotion kararını daha güvenli hale getirmek.
**Demo:** Val iyileşse bile Test-Brier kötüleşen aday promote edilmiyor (`selection_reason=test_brier_degraded`).

## Verification

- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_m003_s03_ensemble_contract.py mania_pipeline/tests/test_run_pipeline_m004_s03_ensemble_robustness_contract.py -q`
- `./venv/Scripts/python -m pytest mania_pipeline/tests -q`

## Tasks

- [x] **T01: Add test-degradation guard to ensemble selection** `est:25m`
- [x] **T02: Add robustness contract test for hold-baseline behavior** `est:25m`
- [x] **T03: Runtime smoke + comparison artifact refresh** `est:25m`
