# S01: Benchmark Lock + Evaluation Harness

**Goal:** M004 başlangıç benchmark’ını kilitlemek ve otomatik önce/sonra kıyas aracını eklemek.
**Demo:** Referans metrik dosyası + karşılaştırma scripti/testi repo içinde mevcut ve çalışıyor.

## Verification

- `./venv/Scripts/python -m pytest mania_pipeline/tests -q`
- `./venv/Scripts/python mania_pipeline/scripts/compare_run_metrics.py --baseline-run mania_pipeline/artifacts/runs_m003/s04_gate/20260314T233549Z_m003_s04_readiness_base --candidate-run mania_pipeline/artifacts/runs_m003/s04_gate/20260314T233640Z_m003_s04_readiness_gate --output-json .gsd/milestones/M004/S01-BENCHMARK-COMPARISON.json`

## Tasks

- [x] **T01: Baseline başarı ölçütlerini kilitle** `est:20m`
- [x] **T02: Run kıyas harness script+test ekle** `est:35m`
- [x] **T03: Benchmark comparison artifact üret** `est:10m`

## Files Likely Touched

- `.gsd/milestones/M004/M004-BASELINE-STATUS.md`
- `mania_pipeline/scripts/compare_run_metrics.py`
- `mania_pipeline/tests/test_compare_run_metrics.py`
