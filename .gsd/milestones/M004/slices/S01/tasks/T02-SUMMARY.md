---
id: T02
parent: S01
milestone: M004
provides:
  - Baseline vs candidate run metrik kıyas scripti + testi.
key_files:
  - mania_pipeline/scripts/compare_run_metrics.py
  - mania_pipeline/tests/test_compare_run_metrics.py
duration: ~30m
verification_result: passed
completed_at: 2026-03-15
blocker_discovered: false
---

# T02: Run kıyas harness script+test ekle

`compare_run_metrics.py` eklendi; iki run_metadata arasında delta brier/logloss/auc hesaplıyor.

Testler:
- `test_compare_run_metrics.py` geçti.
