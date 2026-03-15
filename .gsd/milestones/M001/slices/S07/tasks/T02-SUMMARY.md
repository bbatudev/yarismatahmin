---
id: T02
parent: S07
milestone: M001
provides:
  - Strict submission schema/range validator with fail-fast semantics and persisted validation report.
key_files:
  - mania_pipeline/scripts/run_pipeline.py
  - mania_pipeline/tests/test_run_pipeline_s07_submission_contract.py
key_decisions:
  - D026: submission validation must enforce exact `ID,Pred` columns and numeric [0,1] range.
patterns_established:
  - Validator-report pattern with check-map + status/reason fields.
observability_surfaces:
  - submission_validation_report.json
  - artifact_manifest.json.contracts.submission
duration: ~30m
verification_result: passed
completed_at: 2026-03-15
blocker_discovered: false
---

# T02: Implement strict submission validator and fail-fast semantics

**Implemented strict submission validator and fail-fast enforcement with machine-readable check diagnostics.**

## What Happened

- `_validate_submission_frame` helper eklendi (`columns_exact`, `id_non_null`, `pred_non_null`, `pred_in_range`).
- `_build_optional_submission` helper eklendi:
  - sample submission kaynak dosyası okuma,
  - `submission_<stage>.csv` üretimi,
  - `submission_validation_report.json` yazımı,
  - validation fail path’inde RuntimeError.
- Submission status/path manifest ve stage output yüzeylerine bağlandı.

## Verification

- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_s07_submission_contract.py` ✅

## Diagnostics

- `submission_validation_report.json`
- `artifact_manifest.json -> contracts.submission`

## Deviations

none

## Known Issues

none

## Files Created/Modified

- `mania_pipeline/scripts/run_pipeline.py` — submission validator + report emission + fail-fast path.
- `mania_pipeline/tests/test_run_pipeline_s07_submission_contract.py` — submission schema/range contract tests.
