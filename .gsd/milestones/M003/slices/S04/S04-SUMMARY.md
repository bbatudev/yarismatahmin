---
id: S04
parent: M003
milestone: M003
provides:
  - Policy-gated submission readiness final decision contract.
requires:
  - slice: S03
    provides: ensemble decision surface
affects:
  - none
key_files:
  - mania_pipeline/scripts/run_pipeline.py
  - mania_pipeline/tests/test_run_pipeline_m003_s04_submission_readiness_contract.py
key_decisions:
  - Readiness report-first persistence is mandatory even when artifact stage fails.
patterns_established:
  - Gate fusion artifact with per-check status + blocking/warning reason codes.
observability_surfaces:
  - submission_readiness_report.json
  - run_metadata.json.stage_outputs.artifact.readiness
drill_down_paths:
  - .gsd/milestones/M003/slices/S04/tasks/T01-SUMMARY.md
  - .gsd/milestones/M003/slices/S04/tasks/T02-SUMMARY.md
  - .gsd/milestones/M003/slices/S04/tasks/T03-SUMMARY.md
duration: ~1h20m
verification_result: passed
completed_at: 2026-03-15
---

# S04: Submission Readiness Final Gate

**Artifact stage now emits a unified release-readiness decision (`ready|caution|blocked`) by fusing contract/gate/submission/ensemble signals.**

## What Happened

S04 finalized M003 by adding a single readiness contract surface:
- Added `_evaluate_submission_readiness` to fuse artifact contract, reproducibility, regression gate, policy gate, submission validation, and ensemble aggregate decision.
- Added `submission_readiness_report.json` persistence in artifact stage.
- Ensured readiness report is written before fail-fast raises so blocked runs remain diagnosable.
- Added readiness mirror in artifact stage output (`stage_outputs.artifact.readiness`) and manifest contract map.
- Added S04 contract tests for caution/ready/blocked paths.

## Verification

- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_m003_s04_submission_readiness_contract.py mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py mania_pipeline/tests/test_run_pipeline_s07_submission_contract.py -q` ✅
- `./venv/Scripts/python -m pytest mania_pipeline/tests -q` ✅ (55 passed)
- Runtime proof (isolated root):
  - baseline run (`submission-stage none`) ✅
  - gate run (`submission-stage stage2`) ✅
  - post-run readiness assert ✅ (`status=ready`, submission check passed)

## Requirements Advanced

- none (S04 primarily operationalizes already-validated submission/gate capabilities).

## Requirements Validated

- R012/R018 continuity: submission + gate surfaces now fused under readiness decision report in runtime proofs.

## New Requirements Surfaced

- none

## Requirements Invalidated or Re-scoped

- none

## Deviations

none

## Known Limitations

- First run on a fresh artifacts root typically yields `caution` due to missing historical baselines (expected behavior).

## Follow-ups

- none (M003 scope complete).

## Files Created/Modified

- `mania_pipeline/scripts/run_pipeline.py` — readiness evaluator and artifact integration.
- `mania_pipeline/tests/test_run_pipeline_m003_s04_submission_readiness_contract.py` — S04 contract tests.

## Forward Intelligence

### What the next slice should know
- Readiness decision is now the authoritative release signal; downstream automation should consume this report instead of inferring from multiple files.

### What's fragile
- Baseline-history dependent statuses (`reproducibility`, `regression`) intentionally produce caution/skip on fresh roots; avoid treating these as hard failures.

### Authoritative diagnostics
- First stop: `submission_readiness_report.json` (per-check statuses + blocking/warnings), then gate-specific reports.

### What assumptions changed
- Submission readiness did not require a new pipeline stage; artifact-stage report-first fusion was sufficient.
