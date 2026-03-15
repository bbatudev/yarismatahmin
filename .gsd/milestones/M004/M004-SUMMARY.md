---
id: M004
provides:
  - Benchmark-locked performance workflow with CV-strengthened HPO selection, ensemble robustness guard, and final freeze evidence.
key_decisions:
  - D036 (CV-strengthened HPO objective)
  - D037 (test-degradation-aware ensemble promotion)
  - D038 (no-promotion freeze policy)
patterns_established:
  - Compare-before-promote policy via run-metadata deltas
  - Report-first final freeze evidence bundle
observability_surfaces:
  - `.gsd/milestones/M004/S01-BENCHMARK-COMPARISON.json`
  - `.gsd/milestones/M004/S03-BENCHMARK-COMPARISON.json`
  - `.gsd/milestones/M004/S04-FINAL-COMPARISON.json`
  - `hpo_report.json` (objective + cv diagnostics)
requirement_outcomes:
  - id: R013
    from_status: validated
    to_status: validated
    proof: Final comparison + readiness/submission smoke confirmed no regression promotion.
  - id: R015
    from_status: validated
    to_status: validated
    proof: Submission-stage final smoke produced valid submission and ready status.
duration: 1d
verification_result: passed
completed_at: 2026-03-15
---

# M004: Performance Stabilization & Final Tuning

**Benchmark-locktan final freeze kararına kadar, kalite iyileştirme adımlarını ölçülebilir ve geri alınabilir şekilde tamamladı.**

## What Happened

M004 önce mevcut başarı seviyesini kilitledi, sonra iyileştirme adımlarını tek tek kontrollü devreye aldı:

- S01: baseline benchmark ve run kıyas harness’i eklendi.
- S02: HPO seçim skoru CV-strengthened objective’e geçirildi.
- S03: Ensemble promotion için test-degradation guard eklendi.
- S04: Final smoke + comparison ile no-promotion freeze kararı verildi.

Sonuçta pipeline daha güvenli/izlenebilir hale geldi; ancak final benchmark kıyasında Men tarafında kötüleşme görüldüğü için performans promotion yapılmadı.

## Cross-Slice Verification

- `./venv/Scripts/python -m pytest mania_pipeline/tests -q` → `59 passed`
- `m004_s02_hpo_cv_smoke` run: HPO objective/cv alanları doğrulandı.
- `m004_s03_ensemble_smoke` run: `selection_reason=test_brier_degraded` ile hold-baseline doğrulandı.
- `m004_s04_final_freeze` run: readiness `ready`, submission `passed` (stage2).
- Final compare: `.gsd/milestones/M004/S04-FINAL-COMPARISON.json`.

## Requirement Changes

- R013: validated → validated — Final compare artifact ile promotion kararı kanıtlandı.
- R015: validated → validated — Submission+readiness final smoke kanıtı üretildi.

## Forward Intelligence

### What the next milestone should know
- HPO ve ensemble tarafında karar yüzeyleri artık güçlü; asıl kazanım için feature-level veya split/policy-level yeni sinyal gerekir.

### What's fragile
- Tek run kıyasları sezon varyansına hassas; promotion kararları için multi-run aggregation faydalı olur.

### Authoritative diagnostics
- `compare_run_metrics.py` çıktıları + `submission_readiness_report.json` en güvenilir release sinyali.

### What assumptions changed
- "Robustness iyileştirmeleri doğal olarak performans artışı getirir" varsayımı doğrulanmadı; güvenlik arttı ama Men Brier artışı nedeniyle promotion yapılmadı.

## Files Created/Modified

- `mania_pipeline/scripts/run_pipeline.py` — CV-HPO objective + ensemble test-degradation guard.
- `mania_pipeline/tests/test_run_pipeline_m004_s02_hpo_cv_contract.py` — S02 contract testi.
- `mania_pipeline/tests/test_run_pipeline_m004_s03_ensemble_robustness_contract.py` — S03 robustness testi.
- `.gsd/milestones/M004/S04-FINAL-COMPARISON.json` — final before/after kanıtı.
- `.gsd/milestones/M004/M004-ROADMAP.md` — S01-S04 tamamlandı.
