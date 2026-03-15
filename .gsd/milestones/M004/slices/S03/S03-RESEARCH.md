# S03 — Research

**Date:** 2026-03-15

## Summary

S03 amacı, ensemble seçiminde gereksiz/promosyon hatalarını azaltmak. Salt Val-Brier iyileşmesi, bazı koşularda Test-Brier bozulmasıyla gelebiliyor. Bu durumda non-baseline terfisi üretim riski taşıyor.

Bu nedenle promotion kuralına ek guard kondu: adayın Test Brier’ı baseline’dan kötüleşiyorsa terfi engellenir.

## Recommendation

Promotion yalnızca iki koşul birlikte sağlanınca yapılsın:
1. Val iyileşmesi eşik üstü,
2. Test Brier baseline’dan kötü değil.

## Sources

- `run_pipeline.py::_evaluate_ensemble_candidates_for_gender`
- `test_run_pipeline_m004_s03_ensemble_robustness_contract.py`
