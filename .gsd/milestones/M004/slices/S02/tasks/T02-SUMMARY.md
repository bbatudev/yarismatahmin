---
id: T02
parent: S02
milestone: M004
provides:
  - HPO selection now ranks by objective_score.
key_files:
  - mania_pipeline/scripts/run_pipeline.py
duration: ~25m
verification_result: passed
completed_at: 2026-03-15
blocker_discovered: false
---

# T02: Wire objective score into ranking/payload

Candidate metrics’e `objective_score`, `cv_mean_val_brier`, `generalization_gap` eklendi; best trial objective’e göre seçiliyor.
