---
id: T03
parent: S03
milestone: M004
provides:
  - Runtime smoke proof + benchmark comparison refresh.
key_files:
  - mania_pipeline/artifacts/runs_m004/20260315T000814Z_m004_s03_ensemble_smoke
  - .gsd/milestones/M004/S03-BENCHMARK-COMPARISON.json
duration: ~25m
verification_result: passed
completed_at: 2026-03-15
blocker_discovered: false
---

# T03: Runtime smoke + comparison artifact refresh

`m004_s03_ensemble_smoke` run’ında ensemble decision `hold_baseline` kaldı ve selection reason `test_brier_degraded` olarak doğrulandı.

Comparison sonucu:
- Men Brier: +0.001569 (kötüleşme)
- Women Brier: -0.000085 (iyileşme)
