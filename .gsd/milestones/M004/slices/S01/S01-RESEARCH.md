# S01 — Research

**Date:** 2026-03-15

## Summary

M004 için ilk ihtiyaç, mevcut başarı seviyesini tartışmasız şekilde kilitlemekti. Önce test suite çalıştırılarak repo stabilitesi doğrulandı, ardından referans run’dan Men/Women test metrikleri ve readiness durumu alındı.

İkinci ihtiyaç, sonraki adımlarda “gerçek iyileşme var mı?” sorusunu otomatik cevaplayacak kıyas aracıydı. Bu nedenle run_metadata karşılaştırma scripti eklenerek delta brier/logloss/auc hesapları tek komutla üretilebilir hale getirildi.

## Recommendation

M004 boyunca her performans adımından sonra `compare_run_metrics.py` ile baseline-candidate kıyası zorunlu olsun.

## Existing Code and Patterns

- `mania_pipeline/scripts/run_pipeline.py` — referans metriklerin kaynağı (`stage_outputs.train.metrics_by_split`).
- `mania_pipeline/artifacts/runs_m003/s04_gate/*` — sabit baseline ve readiness referansı.

## Constraints

- Benchmark kilidi bozulmamalı; önce/sonra aynı metrik alanları üzerinden yapılmalı.
- Test suite geçmeden benchmark güncellemesi yapılmamalı.

## Open Risks

- Farklı artifacts root’lardan gelen koşuları kıyaslamak yanlış yorum üretir; eşleşen senaryo kıyaslanmalı.

## Sources

- Run metadata and readiness artifacts from M003 closure runs.
