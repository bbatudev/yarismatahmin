---
estimated_steps: 7
estimated_files: 1
---

# T01: Deterministic ensemble candidate scoring in eval stage

**Slice:** S03 — Ensemble Candidate Integration
**Milestone:** M003

## Description

Eval stage içinde baseline/hpo/blend adaylarını aynı scoring contract’ıyla ölçen ve selection signal üreten helper katmanını ekler.

## Steps

1. Ensemble weight grid ve min-improvement sabitlerini tanımla.
2. Val/Test split probability scoring helper’larını ekle.
3. HPO best override’tan candidate model retrain helper’ını ekle.
4. Blend candidate scoring (weight sweep) ekle.
5. Deterministic selection rule (Val Brier + improvement threshold) uygula.
6. `ensemble_report.json` üret.
7. Eval payload summary mirror’ı döndür.

## Must-Haves

- [x] Candidate ledger reason-coded status alanlarıyla persist edilir.
- [x] Baseline dışı seçim threshold ile guard edilir.

## Verification

- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_m003_s03_ensemble_contract.py -q`

## Inputs

- `mania_pipeline/scripts/run_pipeline.py` — existing eval/calibration/hpo seams.

## Expected Output

- `mania_pipeline/scripts/run_pipeline.py` — ensemble scoring + report helpers.
