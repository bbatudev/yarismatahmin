---
id: S03
parent: M002
milestone: M002
provides:
  - Multi-evidence governance decision contract fused from ablation, drift, and calibration policy outputs.
requires:
  - slice: S01
    provides: drift regime signals
  - slice: S02
    provides: calibration policy payload and report
affects:
  - S04
key_files:
  - mania_pipeline/scripts/run_pipeline.py
  - mania_pipeline/tests/test_run_pipeline_m002_s03_governance_decision_contract.py
  - mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py
  - mania_pipeline/tests/test_run_pipeline_s07_submission_contract.py
key_decisions:
  - Governance decision surface is deterministic and reason-coded with a fixed decision domain.
patterns_established:
  - New eval reports must be mirrored and contract-enforced at artifact stage.
observability_surfaces:
  - governance_decision_report.json
  - eval_report.json.governance_decision
  - run_metadata.json.stage_outputs.eval_report.governance_decision
drill_down_paths:
  - .gsd/milestones/M002/slices/S03/tasks/T01-SUMMARY.md
  - .gsd/milestones/M002/slices/S03/tasks/T02-SUMMARY.md
  - .gsd/milestones/M002/slices/S03/tasks/T03-SUMMARY.md
duration: ~1h15m
verification_result: passed
completed_at: 2026-03-15
---

# S03: Governance Decision Fusion (Ablation + Drift + Calibration)

**Canonical eval flow now emits a reason-coded governance decision report that fuses ablation, drift, and calibration policy evidence.**

## What Happened

S03 introduced governance decision fusion as a dedicated contract surface:
- Gender-level decision payloads now include `decision`, `confidence`, `reason_codes`, and `evidence_bundle`.
- Evidence bundle joins three canonical signals: ablation deltas, drift alerts/gaps, calibration policy selection effects.
- Aggregate decision rollup is emitted for control-plane consumption.
- Decision artifact (`governance_decision_report.json`) is persisted and mirrored under eval payloads.

Artifact-stage required contract surface was expanded with `governance_decision_report_json`, and S06/S07 fixtures were updated to remain synchronized with required report list.

## Verification

- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_m002_s03_governance_decision_contract.py mania_pipeline/tests/test_run_pipeline_s05_governance_contract.py mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py mania_pipeline/tests/test_run_pipeline_s07_submission_contract.py -q` ✅
- `./venv/Scripts/python -m pytest mania_pipeline/tests -q` ✅
- `./venv/Scripts/python mania_pipeline/scripts/run_pipeline.py --seed 42 --run-label m002_s03_decision_smoke` ✅
- post-run governance decision artifact/payload assert ✅

## Requirements Advanced

- R018 — Regression/policy observability için governance karar yüzeyi multi-evidence hale getirildi.

## Requirements Validated

- none

## New Requirements Surfaced

- none

## Requirements Invalidated or Re-scoped

- none

## Deviations

none

## Known Limitations

- Decision confidence hesaplaması heuristik başlangıç formülü.
- S03’te decision surface üretildi; gate behavior coupling S04 scope’unda.

## Follow-ups

- S04’te regression gate kararını governance decision reason-codes ile birlikte enforce et.
- Confidence tuning için historical run dağılımına göre threshold stratejisi belirle.

## Files Created/Modified

- `mania_pipeline/scripts/run_pipeline.py` — governance decision fusion + report emission + artifact requirement.
- `mania_pipeline/tests/test_run_pipeline_m002_s03_governance_decision_contract.py` — S03 contract test.
- `mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py` — required artifact fixture sync.
- `mania_pipeline/tests/test_run_pipeline_s07_submission_contract.py` — required artifact fixture sync.
- `.gsd/milestones/M002/slices/S03/S03-PLAN.md` — completed task tracking.

## Forward Intelligence

### What the next slice should know
- Governance decision payload already provides reason-coded fusion output, so S04 can consume directly without rebuilding evidence extraction.

### What's fragile
- Confidence scoring coefficients are hand-tuned; small metric noise can shift confidence bands.

### Authoritative diagnostics
- Primary surface: `run_metadata.json.stage_outputs.eval_report.governance_decision`.

### What assumptions changed
- Governance fusion did not require changes in upstream ablation/drift/policy producers; eval-stage composition was sufficient.
