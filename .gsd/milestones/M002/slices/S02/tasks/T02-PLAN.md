---
estimated_steps: 5
estimated_files: 3
---

# T02: Wire policy artifact and enforce artifact contract

**Slice:** S02 — Regime-Aware Calibration Policy Engine
**Milestone:** M002

## Description

Policy çıktısını canonical eval payload’a ve artifact contract required-surface listesine bağlar; mevcut S06/S07 fixture’larını yeni required artifact ile hizalar.

## Steps

1. `calibration_policy_report.json` üretimini eval stage’e ekle.
2. `eval_report` return/persist payload’ına `calibration_policy` bloğunu ekle.
3. `stage_artifact` required artifact listesine `calibration_policy_report_json` ekle.
4. S06/S07 test fixture context’lerine policy report path’i ekle.
5. İlgili contract testlerini çalıştır.

## Must-Haves

- [x] Policy report path artifact contract içinde required olmalı.
- [x] S06/S07 testleri yeni required artifact ile geçmeli.

## Verification

- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py mania_pipeline/tests/test_run_pipeline_s07_submission_contract.py -q`

## Inputs

- `mania_pipeline/scripts/run_pipeline.py` — stage eval/artifact wiring.
- `mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py` — required artifact fixture.
- `mania_pipeline/tests/test_run_pipeline_s07_submission_contract.py` — submission fixture contract.

## Expected Output

- `mania_pipeline/scripts/run_pipeline.py` — policy payload + artifact required path.
- `mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py` — fixture alignment.
- `mania_pipeline/tests/test_run_pipeline_s07_submission_contract.py` — fixture alignment.
