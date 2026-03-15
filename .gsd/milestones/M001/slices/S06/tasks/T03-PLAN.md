---
estimated_steps: 5
estimated_files: 3
---

# T03: Implement previous-run regression gate and wire statuses into manifest/metadata

**Slice:** S06 — Artifact Contract + Reproducibility + Regression Gate
**Milestone:** M001

## Description

Önceki başarılı run’a göre Brier/calibration/AUC delta değerlendirilir; `regression_gate_report.json` üretilir ve manifest/metadata surface’larına status’ler bağlanır.

## Steps

1. Regression gate evaluator helper’ını yaz.
2. Brier mandatory + calibration fail + AUC informational policy’sini uygula.
3. `regression_gate_report.json` üret.
4. Manifest ve stage_outputs.artifact içinde status/path wiring yap.
5. Blocking failure’da stage fail semantics uygula.

## Must-Haves

- [x] Gate pass/fail/skip kararı machine-readable raporda persist edilir.
- [x] AUC deltası informational olarak raporlanır, karar kuralını bloke etmez.

## Verification

- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py -k "regression"`
- `./venv/Scripts/python mania_pipeline/scripts/run_pipeline.py --seed 42 --run-label s06_contract_smoke`

## Observability Impact

- Signals added/changed: `stage_outputs.artifact.regression_gate.status`
- How a future agent inspects this: `regression_gate_report.json` + `artifact_manifest.json.contracts`
- Failure state exposed: `blocking_failures` listesi

## Inputs

- `mania_pipeline/scripts/run_pipeline.py` — artifact stage
- `.gsd/DECISIONS.md` — D005 regression gate policy

## Expected Output

- `mania_pipeline/scripts/run_pipeline.py` — regression evaluator + manifest wiring
- `mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py` — regression fail/pass testleri
- `mania_pipeline/artifacts/runs/<run_id>/regression_gate_report.json` — runtime report
