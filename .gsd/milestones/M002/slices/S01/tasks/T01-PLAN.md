---
estimated_steps: 5
estimated_files: 2
---

# T01: Add deterministic drift summary helpers and regime segmentation

**Slice:** S01 — Regime Drift Baseline & Signal Contract
**Milestone:** M002

## Description

Split bazlı drift summary ve test split regime segmentasyon helper’ları eklenir; alert reason domain belirlenir.

## Steps

1. Split summary helper (`sample_count`, `pred_mean`, `actual_rate`, `gap`) yaz.
2. `SeedNum_diff` tabanlı regime bucket helper’ı (`close|medium|wide`) ekle.
3. Regime summary hesapla.
4. Alert logic ekle (`test_gap_shift`, `low_sample_regime`).
5. Unit-level contract testleri yaz.

## Must-Haves

- [ ] Helper çıktıları deterministic schema ile döner.
- [ ] Alert reason’ları explicit domain içinde kalır.

## Verification

- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_m002_s01_drift_contract.py -k "helpers"`

## Observability Impact

- Signals added/changed: drift `alerts` listesi
- How a future agent inspects this: `drift_regime_report.json`
- Failure state exposed: düşük örnekli regime ve split gap shift reason-code’ları

## Inputs

- `mania_pipeline/scripts/run_pipeline.py` — eval scoring loop
- `.gsd/milestones/M002/slices/S01/S01-RESEARCH.md` — regime segmentation recommendation

## Expected Output

- `mania_pipeline/scripts/run_pipeline.py` — drift helper functions
- `mania_pipeline/tests/test_run_pipeline_m002_s01_drift_contract.py` — helper contract tests
