---
estimated_steps: 6
estimated_files: 2
---

# T01: Deterministic regime-aware selector helpers

**Slice:** S02 — Regime-Aware Calibration Policy Engine
**Milestone:** M002

## Description

Eval stage içinde calibration policy seçimini taşıyan helper setini kurar: method availability, candidate scoring, regime-based method order ve deterministic selected_method üretimi.

## Steps

1. Policy constants tanımla (`methods`, `min_val_samples`, `min_improvement`).
2. Candidate scoring helper’ı (Brier/LogLoss/AUC/ECE/WMAE) ekle.
3. `none/platt/isotonic` calibrator uygulama helper’ını reason-coded unavailable davranışıyla yaz.
4. Drift regime’den method order türet.
5. Gender bazında candidate payload + selected method + selection_reason üret.
6. Contract test dosyasında helper davranışlarını doğrula.

## Must-Haves

- [x] Unavailable methods için reason zorunlu.
- [x] Selection deterministik ve stable ordering ile çalışır.

## Verification

- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_m002_s02_calibration_policy_contract.py -q`

## Inputs

- `mania_pipeline/scripts/run_pipeline.py` — mevcut eval/calibration/drift akışı.
- `.gsd/milestones/M002/slices/S01/S01-SUMMARY.md` — drift surface contract.

## Expected Output

- `mania_pipeline/scripts/run_pipeline.py` — selector helper implementation.
- `mania_pipeline/tests/test_run_pipeline_m002_s02_calibration_policy_contract.py` — helper contract checks.
