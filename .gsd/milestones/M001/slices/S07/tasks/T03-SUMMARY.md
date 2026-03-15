---
id: T03
parent: S07
milestone: M001
provides:
  - Final integration proof for submission-enabled canonical run and M001 closure updates.
key_files:
  - .gsd/REQUIREMENTS.md
  - .gsd/milestones/M001/M001-ROADMAP.md
  - .gsd/milestones/M001/slices/S07/S07-SUMMARY.md
  - mania_pipeline/artifacts/runs/<run_id>/submission_stage2.csv
key_decisions:
  - D027: S07 final acceptance requires submission-enabled runtime proof, not test-only evidence.
patterns_established:
  - Runtime-first closure pattern for milestone completion claims.
observability_surfaces:
  - stage_outputs.artifact.submission
  - submission_stage2.csv + submission_validation_report.json
duration: ~30m
verification_result: passed
completed_at: 2026-03-15
blocker_discovered: false
---

# T03: Prove final integration runtime with submission enabled and update milestone state

**Validated submission-enabled canonical runtime and updated milestone/requirement state to reflect M001 completion.**

## What Happened

- Submission-enabled smoke run alındı (`--submission-stage stage2`).
- Run artifact assert’leriyle submission schema/range doğrulandı.
- Requirement/roadmap/project/state dosyaları milestone kapanışını yansıtacak şekilde güncellendi.

## Verification

- `./venv/Scripts/python mania_pipeline/scripts/run_pipeline.py --seed 42 --run-label s07_submission_smoke --submission-stage stage2` ✅
- `./venv/Scripts/python -m pytest mania_pipeline/tests -q` ✅
- post-run script assertion (`ID,Pred`, [0,1], submission status=passed) ✅

## Diagnostics

- `run_metadata.json -> stage_outputs.artifact.submission`
- `submission_stage2.csv`
- `submission_validation_report.json`

## Deviations

none

## Known Issues

none

## Files Created/Modified

- `.gsd/REQUIREMENTS.md` — R012 validated.
- `.gsd/milestones/M001/M001-ROADMAP.md` — S07 marked complete.
- `.gsd/milestones/M001/slices/S07/S07-SUMMARY.md` — final assembly proof.
