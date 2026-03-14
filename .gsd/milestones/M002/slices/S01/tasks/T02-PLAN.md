---
estimated_steps: 4
estimated_files: 2
---

# T02: Emit drift artifact and wire into eval/metadata contracts

**Slice:** S01 — Regime Drift Baseline & Signal Contract
**Milestone:** M002

## Description

Drift hesaplarının artifact olarak persist edilmesi ve eval payload’a mirror edilmesi.

## Steps

1. `drift_regime_report.json` emission ekle.
2. `eval_report` payload’a `drift` bloğunu ekle.
3. `stage_outputs.eval_report.drift` return surface’ını ekle.
4. Contract test assertionlarını tamamla.

## Must-Haves

- [x] Drift artifact dosyası canonical run’da oluşur.
- [x] Eval report ve stage output aynı drift report path’i taşır.

## Verification

- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_m002_s01_drift_contract.py`

## Inputs

- `mania_pipeline/scripts/run_pipeline.py` — stage_eval_report flow
- `mania_pipeline/tests/test_run_pipeline_m002_s01_drift_contract.py` — contract test seam

## Expected Output

- `mania_pipeline/scripts/run_pipeline.py` — drift artifact + payload wiring
- `mania_pipeline/tests/test_run_pipeline_m002_s01_drift_contract.py` — wiring assertions
