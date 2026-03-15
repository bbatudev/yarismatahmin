---
id: S07
parent: M001
milestone: M001
provides:
  - Optional submission generation + strict validation integrated into canonical artifact stage with final runtime proof.
requires:
  - slice: S06
    provides: Artifact-stage gate/report infrastructure (`artifact_contract`, `reproducibility`, `regression_gate`).
affects:
  - M002
key_files:
  - mania_pipeline/scripts/run_pipeline.py
  - mania_pipeline/tests/test_run_pipeline_s07_submission_contract.py
  - .gsd/REQUIREMENTS.md
  - .gsd/milestones/M001/M001-ROADMAP.md
  - .gsd/PROJECT.md
  - .gsd/STATE.md
key_decisions:
  - D025: submission remains optional via `--submission-stage`.
  - D026: strict `ID,Pred` validation contract is blocking.
  - D027: milestone closure requires submission-enabled runtime proof.
patterns_established:
  - Optional-output contract pattern: skip with reason when disabled, strict validation when enabled.
observability_surfaces:
  - submission_stage2.csv
  - submission_validation_report.json
  - run_metadata.json (`stage_outputs.artifact.submission`)
  - artifact_manifest.json (`contracts.submission`)
drill_down_paths:
  - .gsd/milestones/M001/slices/S07/tasks/T01-SUMMARY.md
  - .gsd/milestones/M001/slices/S07/tasks/T02-SUMMARY.md
  - .gsd/milestones/M001/slices/S07/tasks/T03-SUMMARY.md
duration: ~1h30m
verification_result: passed
completed_at: 2026-03-15
---

# S07: Optional Submission Validation + Final Integration

**Canonical pipeline now supports optional submission generation with strict schema validation, and M001 final integration is runtime-proven end-to-end.**

## What Happened

S07 introduced submission as an explicit optional branch in `stage_artifact`:
- CLI flag: `--submission-stage {none,stage1,stage2}`
- `none` keeps default behavior and writes reason-coded skip validation report.
- `stage1|stage2` generates `submission_<stage>.csv` from Kaggle sample IDs and validates strict `ID,Pred` schema/range/null constraints.

Submission status/report paths are now mirrored in `stage_outputs.artifact.submission` and `artifact_manifest.json.contracts.submission`.

## Verification

- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_s07_submission_contract.py` ✅
- `./venv/Scripts/python -m pytest mania_pipeline/tests -q` ✅
- `./venv/Scripts/python mania_pipeline/scripts/run_pipeline.py --seed 42 --run-label s07_submission_smoke --submission-stage stage2` ✅
- post-run assertion: submission status passed, columns `ID,Pred`, `Pred` in `[0,1]` ✅

Proof run: `mania_pipeline/artifacts/runs/20260314T212534Z_s07_submission_smoke/`

## Requirements Advanced

- none

## Requirements Validated

- R012 — Optional submission generation and strict format validation now runtime-validated.

## New Requirements Surfaced

- none

## Requirements Invalidated or Re-scoped

- none

## Deviations

none

## Known Limitations

- Submission prediction values currently deterministic placeholder probabilities (`0.5`) and are format-focused, not performance-optimized.

## Follow-ups

- M002’de submission `Pred` üretimini model-based inference pipeline ile zenginleştir (format kontratı korunarak).

## Files Created/Modified

- `mania_pipeline/scripts/run_pipeline.py` — submission builder/validator and artifact wiring.
- `mania_pipeline/tests/test_run_pipeline_s07_submission_contract.py` — submission contract tests.
- `.gsd/REQUIREMENTS.md` — R012 validated.
- `.gsd/milestones/M001/M001-ROADMAP.md` — S07 marked complete.
- `.gsd/PROJECT.md` — current state updated for M001 closure.
- `.gsd/STATE.md` — next milestone handoff state.

## Forward Intelligence

### What the next slice should know
- Artifact stage now has four contract surfaces: artifact contract, reproducibility, regression, submission.

### What's fragile
- Submission quality is intentionally simplistic; competition-performance work still depends on a dedicated inference layer.

### Authoritative diagnostics
- `run_metadata.json.stage_outputs.artifact.submission` and `submission_validation_report.json` are the first-check surfaces.

### What assumptions changed
- “Submission handling ayrı bir script olmalı” — canonical artifact stage içine entegre etmek daha izlenebilir ve güvenli oldu.
