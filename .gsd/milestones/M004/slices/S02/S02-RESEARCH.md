# S02 — Research

**Date:** 2026-03-15

## Summary

S02 odak noktası, HPO seçiminde tek split Val sinyalinin kırılganlığını azaltmak. Bunun için her trial için ek CV benzeri fold değerlendirmesi hesaplanıp objective olarak kullanıldı.

Yeni objective: başarılı fold’lardan gelen ortalama Val Brier. CV çalışamazsa fallback olarak `val_brier + gap_penalty` kullanılıyor.

## Recommendation

HPO seçiminde `objective_score` ana sıralama metriği olsun; `val_brier` yalnızca tie-breaker olarak kalsın.

## Sources

- `run_pipeline.py::_run_hpo_search_for_gender`
- New contract test: `test_run_pipeline_m004_s02_hpo_cv_contract.py`
