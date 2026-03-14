---
id: T01
parent: S04
milestone: M003
provides:
  - Artifact-stage submission readiness fusion report.
key_files:
  - mania_pipeline/scripts/run_pipeline.py
key_decisions:
  - Readiness report is written before fail-fast raises to preserve diagnostics on blocked runs.
patterns_established:
  - report-first diagnostics for blocking gate failures.
observability_surfaces:
  - submission_readiness_report.json
duration: ~35m
verification_result: passed
completed_at: 2026-03-15
blocker_discovered: false
---

# T01: Readiness evaluator and artifact wiring

**Added submission readiness evaluator and wired it into artifact-stage outputs/manifests.**

## What Happened

- Added `_evaluate_submission_readiness(...)` helper with `ready|caution|blocked` semantics.
- Added pre-submission blocker flow so readiness can be computed even when upstream gates fail.
- Persisted `submission_readiness_report.json` before fail-fast exceptions.
- Added `readiness` section to artifact stage return payload and manifest contracts map.

## Verification

- New readiness tests passed ✅

## Diagnostics

- `submission_readiness_report.json` now exists on both success and failure paths.

## Deviations

none

## Known Issues

none

## Files Created/Modified

- `mania_pipeline/scripts/run_pipeline.py` — readiness helper + artifact wiring.
