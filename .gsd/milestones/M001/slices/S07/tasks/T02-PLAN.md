---
estimated_steps: 4
estimated_files: 2
---

# T02: Implement strict submission validator and fail-fast semantics

**Slice:** S07 — Optional Submission Validation + Final Integration
**Milestone:** M001

## Description

Submission dataframe için `ID,Pred` exact schema, null ve range doğrulaması eklenir; invalid durumda stage fail enforce edilir.

## Steps

1. Submission validator helper’ı ekle.
2. Validation report payload’ını standardize et.
3. Validation fail durumunda RuntimeError üret.
4. Manifest/stage output’a submission status/ref bağla.

## Must-Haves

- [x] Validation check listesi report içinde machine-readable bulunur.
- [x] Invalid submission deterministic fail reason üretir.

## Verification

- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_s07_submission_contract.py`

## Observability Impact

- Signals added/changed: `stage_outputs.artifact.submission.status`
- How a future agent inspects this: `submission_validation_report.json`
- Failure state exposed: validation `checks` map + `status=failed`

## Inputs

- `mania_pipeline/scripts/run_pipeline.py` — artifact stage reports pattern (S06)
- `.gsd/milestones/M001/slices/S06/S06-SUMMARY.md` — report-first fail-fast pattern

## Expected Output

- `mania_pipeline/scripts/run_pipeline.py` — strict validator + fail-fast path
- `mania_pipeline/tests/test_run_pipeline_s07_submission_contract.py` — schema/range validation assertions
