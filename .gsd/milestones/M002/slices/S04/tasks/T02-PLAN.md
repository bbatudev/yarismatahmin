---
estimated_steps: 5
estimated_files: 3
---

# T02: Policy gate report wiring

**Slice:** S04 — Policy-Gated Final Integration
**Milestone:** M002

## Description

Stage artifact içinde policy gate integration raporu üretir ve contract yüzeylerine bağlar.

## Steps

1. `policy_gate_report.json` payload’ını oluştur.
2. Manifest `contracts` içine policy gate entry ekle.
3. `stage_artifact` return payload’ına policy gate bloğunu ekle.
4. Existing artifact/submission tests ile uyumu doğrula.
5. Diagnostics yüzeylerini dokümante et.

## Must-Haves

- [x] Policy gate report path return ve manifest üzerinden erişilebilir.
- [x] Existing contract testleri regress etmez.

## Verification

- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py mania_pipeline/tests/test_run_pipeline_s07_submission_contract.py -q`

## Inputs

- `mania_pipeline/scripts/run_pipeline.py` — stage_artifact manifest/return behavior.
- `mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py` — artifact contract baseline checks.
- `mania_pipeline/tests/test_run_pipeline_s07_submission_contract.py` — submission path checks.

## Expected Output

- `mania_pipeline/scripts/run_pipeline.py` — policy gate report emission.
- `mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py` — compatibility verified.
- `mania_pipeline/tests/test_run_pipeline_s07_submission_contract.py` — compatibility verified.
