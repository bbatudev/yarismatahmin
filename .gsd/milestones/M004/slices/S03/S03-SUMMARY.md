# S03: Ensemble Robustness Rules

Ensemble promotion kararına test-degradation guard eklendi.

## Yapılanlar
- Non-baseline promotion artık val-threshold + test non-degradation ile gated.
- Yeni robustness contract testi eklendi.
- Runtime smoke (`20260315T000814Z_m004_s03_ensemble_smoke`) ve comparison artifact (`S03-BENCHMARK-COMPARISON.json`) üretildi.

## Sonuç
Selection reason her iki gender için de `test_brier_degraded` ile baseline’da kaldı; gereksiz promotion engeli aktif.
