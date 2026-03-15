---
estimated_steps: 5
estimated_files: 2
---

# T02: Implement reproducibility tolerance gate with same commit+seed baseline lookup

**Slice:** S06 — Artifact Contract + Reproducibility + Regression Gate
**Milestone:** M001

## Description

Aynı commit+seed için son başarılı baseline run bulunur; Test Brier deltası toleransla karşılaştırılır ve `reproducibility_report.json` üretilir.

## Steps

1. Prior successful run metadata loader ekle.
2. Current/baseline metric snapshot helper’ı yaz.
3. `|ΔBrier|<=1e-4` kuralını gender bazında uygula.
4. `reproducibility_report.json` yaz.
5. Breach durumunda stage fail et.

## Must-Haves

- [x] Baseline yoksa reason-coded `skipped` döner.
- [x] Breach durumunda fail state açık reason/failure listesi taşır.

## Verification

- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py -k "repro"`
- `./venv/Scripts/python mania_pipeline/scripts/run_pipeline.py --seed 42 --run-label s06_repro_check`

## Observability Impact

- Signals added/changed: `stage_outputs.artifact.reproducibility.status`
- How a future agent inspects this: `reproducibility_report.json`
- Failure state exposed: `reason`, `failures`, gender bazlı delta/tolerance durumu

## Inputs

- `mania_pipeline/scripts/run_pipeline.py` — artifact stage + run metadata seam
- `.gsd/DECISIONS.md` — D004 reproducibility tolerance kararı

## Expected Output

- `mania_pipeline/scripts/run_pipeline.py` — reproducibility evaluator + gate fail semantics
- `mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py` — reproducibility pass/fail testleri
