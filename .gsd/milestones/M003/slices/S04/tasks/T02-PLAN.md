---
estimated_steps: 4
estimated_files: 1
---

# T02: Readiness contract tests

**Slice:** S04 — Submission Readiness Final Gate
**Milestone:** M003

## Description

S04 readiness karar yollarını (`ready|caution|blocked`) deterministic fixture’larla test eder.

## Steps

1. Caution case testini ekle (submission not requested).
2. Ready case testini ekle (submission pass + gates pass).
3. Blocked case testini ekle (gate fail path + readiness report persisted).
4. Regression impact suite’ini çalıştır.

## Must-Haves

- [x] Üç readiness statüsü için contract coverage sağlanır.
- [x] Blocked durumda readiness report varlığı assert edilir.

## Verification

- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_m003_s04_submission_readiness_contract.py mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py mania_pipeline/tests/test_run_pipeline_s07_submission_contract.py -q`

## Inputs

- `mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py` — artifact fixture pattern.

## Expected Output

- `mania_pipeline/tests/test_run_pipeline_m003_s04_submission_readiness_contract.py`
