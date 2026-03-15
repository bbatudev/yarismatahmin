---
id: T01
parent: S07
milestone: M001
provides:
  - Optional submission-stage CLI flag and artifact-stage submission branch wiring.
key_files:
  - mania_pipeline/scripts/run_pipeline.py
  - mania_pipeline/tests/test_run_pipeline_s07_submission_contract.py
key_decisions:
  - D025: submission generation remains optional via explicit CLI stage flag.
patterns_established:
  - Optional branch pattern in artifact stage (`none` => skip report, no side effects).
observability_surfaces:
  - stage_outputs.artifact.submission.status
  - submission_validation_report.json
duration: ~25m
verification_result: passed
completed_at: 2026-03-15
blocker_discovered: false
---

# T01: Add optional submission stage argument and builder flow in artifact stage

**Added `--submission-stage` runtime control and wired optional submission flow into artifact stage without changing default behavior.**

## What Happened

- `parse_args` içine `--submission-stage` (`none|stage1|stage2`) eklendi.
- `main` context’ine `submission_stage` geçirildi.
- Artifact stage’de optional submission builder çağrısı eklendi.

## Verification

- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_s07_submission_contract.py -k "skips"` ✅

## Diagnostics

- `run_metadata.json -> stage_outputs.artifact.submission`

## Deviations

none

## Known Issues

none

## Files Created/Modified

- `mania_pipeline/scripts/run_pipeline.py` — CLI arg + artifact stage submission wiring.
- `mania_pipeline/tests/test_run_pipeline_s07_submission_contract.py` — skip path test.
