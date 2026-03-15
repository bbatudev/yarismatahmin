---
id: T01
parent: S06
milestone: M001
provides:
  - Artifact stage required-file contract report with fail-fast enforcement.
key_files:
  - mania_pipeline/scripts/run_pipeline.py
  - mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py
key_decisions:
  - D024: artifact contract is enforced in `stage_artifact` using persisted report + fail-fast semantics.
patterns_established:
  - Contract report pattern: write report first, then fail with explicit missing list.
observability_surfaces:
  - artifact_contract_report.json
  - stage_outputs.artifact.artifact_contract.status
duration: ~35m
verification_result: passed
completed_at: 2026-03-15
blocker_discovered: false
---

# T01: Add artifact contract report and required-file enforcement in artifact stage

**Added required-artifact contract emission and fail-fast enforcement to the canonical artifact stage.**

## What Happened

- `stage_artifact` içine required artifact haritası eklendi (metadata/events/eval/calibration/governance/model/feature dosyaları).
- `artifact_contract_report.json` yazımı eklendi.
- Missing artifact olduğunda stage `RuntimeError` ile fail edecek şekilde enforcement eklendi.
- Contract status ve report path manifest + stage output yüzeyine bağlandı.

## Verification

- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py -k "contract"` ✅

## Diagnostics

- `mania_pipeline/artifacts/runs/<run_id>/artifact_contract_report.json`
- `run_metadata.json -> stage_outputs.artifact.artifact_contract`

## Deviations

none

## Known Issues

none

## Files Created/Modified

- `mania_pipeline/scripts/run_pipeline.py` — artifact contract report + required-file fail enforcement.
- `mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py` — contract case assertions.
