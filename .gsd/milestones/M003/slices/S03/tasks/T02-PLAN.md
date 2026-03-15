---
estimated_steps: 5
estimated_files: 4
---

# T02: Eval/artifact wiring for ensemble contract

**Slice:** S03 — Ensemble Candidate Integration
**Milestone:** M003

## Description

Ensemble yüzeyini eval return payload ve artifact required-artefact kontratına bağlar; mevcut artifact tests fixture’larını yeni required path’e uyumlar.

## Steps

1. `eval_report` payloadına `ensemble` alanını ekle.
2. `stage_eval_report` return payloadında `ensemble` mirror ekle.
3. `stage_artifact` required artifact listesine `ensemble_report_json` ekle.
4. S06/S07/M002-S04 fixture context’lerine ensemble report path ekle.
5. Kontrat testlerini çalıştır.

## Must-Haves

- [x] Ensemble report artık artifact contract’in parçasıdır.
- [x] Legacy fixture testleri yeni kontrata göre geçer.

## Verification

- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py mania_pipeline/tests/test_run_pipeline_s07_submission_contract.py mania_pipeline/tests/test_run_pipeline_m002_s04_policy_gate_contract.py -q`

## Inputs

- `mania_pipeline/scripts/run_pipeline.py`
- `mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py`

## Expected Output

- `mania_pipeline/scripts/run_pipeline.py`
- `mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py`
- `mania_pipeline/tests/test_run_pipeline_s07_submission_contract.py`
- `mania_pipeline/tests/test_run_pipeline_m002_s04_policy_gate_contract.py`
