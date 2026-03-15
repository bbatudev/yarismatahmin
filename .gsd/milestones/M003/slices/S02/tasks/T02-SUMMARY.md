---
id: T02
parent: S02
milestone: M003
provides:
  - HPO CLI/config wiring and machine-readable hpo report payload.
key_files:
  - mania_pipeline/scripts/run_pipeline.py
  - mania_pipeline/tests/test_run_pipeline_m003_s02_hpo_contract.py
key_decisions:
  - Always write `hpo_report.json` (including skipped) for consistent diagnostics surface.
patterns_established:
  - Optional heavy workflows expose `status=skipped|passed|failed` under stable report schema.
observability_surfaces:
  - stage_outputs.train.hpo
  - hpo_report.json
duration: ~25m
verification_result: passed
completed_at: 2026-03-15
blocker_discovered: false
---

# T02: Emit hpo_report artifact and wire into train payload/CLI

**Wired HPO configuration through CLI/context and persisted train-stage HPO report surfaces.**

## What Happened

- Added CLI args: `--hpo-trials`, `--hpo-target-profile`.
- Stored HPO config in run context/metadata.
- Added `stage_outputs.train.hpo` payload block and `hpo_report.json` persistence.
- Added contract tests for CLI/HPO payload/report behavior.

## Verification

- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_m003_s02_hpo_contract.py -q` ✅

## Diagnostics

- Report path: `stage_outputs.train.hpo.report_json`.

## Deviations

none

## Known Issues

none

## Files Created/Modified

- `mania_pipeline/scripts/run_pipeline.py` — CLI+payload report wiring.
- `mania_pipeline/tests/test_run_pipeline_m003_s02_hpo_contract.py` — contract tests.
