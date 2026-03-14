---
id: S05
parent: M001
milestone: M001
provides:
  - Canonical governance layer with deterministic ledger + controlled ablation artifacts wired into eval and metadata contracts.
requires:
  - slice: S03
    provides: Stable train payload (`genders.*.model_path`, `feature_snapshot`, `metrics_by_split`) and single execution path enforcement.
affects:
  - S06
key_files:
  - mania_pipeline/scripts/feature_governance.py
  - mania_pipeline/scripts/run_pipeline.py
  - mania_pipeline/tests/test_feature_governance_ledger.py
  - mania_pipeline/tests/test_feature_governance_ablation.py
  - mania_pipeline/tests/test_run_pipeline_s05_governance_contract.py
  - .gsd/REQUIREMENTS.md
  - .gsd/milestones/M001/M001-ROADMAP.md
  - .gsd/PROJECT.md
  - .gsd/STATE.md
key_decisions:
  - D020: governance/ablation stays inside `stage_eval_report` (no new stage).
  - D021: deterministic capped suspicious-group retrain policy.
  - D023: skip-reason taxonomy + governance summary counters are contract-locked.
patterns_established:
  - Eval-stage extension pattern reused for governance + ablation artifact emission while preserving topology lock.
  - Governance module now owns deterministic selection/delta primitives; orchestrator owns runtime scoring and persistence.
observability_surfaces:
  - mania_pipeline/artifacts/runs/<run_id>/governance_ledger.csv
  - mania_pipeline/artifacts/runs/<run_id>/ablation_report.json
  - mania_pipeline/artifacts/runs/<run_id>/eval_report.json (`governance` block)
  - mania_pipeline/artifacts/runs/<run_id>/run_metadata.json (`stage_outputs.eval_report.governance`)
  - mania_pipeline/artifacts/runs/<run_id>/stage_events.jsonl
drill_down_paths:
  - .gsd/milestones/M001/slices/S05/tasks/T01-SUMMARY.md
  - .gsd/milestones/M001/slices/S05/tasks/T02-SUMMARY.md
  - .gsd/milestones/M001/slices/S05/tasks/T03-SUMMARY.md
duration: ~3h
verification_result: passed
completed_at: 2026-03-15
---

# S05: Feature Governance + Controlled Ablation

**Canonical pipeline now emits machine-readable feature governance and controlled ablation deltas in the eval contract, including deterministic skip diagnostics, without changing stage topology.**

## What Happened

S05 shipped in three tasks:
- **T01** established governance ledger generation (`feature/group/default_action/evidence`) with deterministic policy and women-side men-only exclusion.
- **T02** implemented controlled suspicious-group retrain, split-aware delta computation (Val/Test: ΔBrier, ΔLogLoss, ΔAUC, ΔCalibration), and bounded deterministic group selection.
- **T03** finalized runtime wiring and proof: governance artifacts/summary now appear in both `eval_report.json` and `run_metadata.json.stage_outputs.eval_report` with stable diagnostics fields.

The canonical stage list stayed unchanged (`feature`, `train`, `eval_report`, `artifact`).

## Verification

- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_feature_governance_ledger.py mania_pipeline/tests/test_feature_governance_ablation.py mania_pipeline/tests/test_run_pipeline_s05_governance_contract.py mania_pipeline/tests/test_run_pipeline_cli.py mania_pipeline/tests/test_run_pipeline_s04_calibration_contract.py -q` ✅
- `./venv/Scripts/python mania_pipeline/scripts/run_pipeline.py --seed 42 --run-label s05_governance_smoke` ✅
- Post-run assertions for artifact presence + executed group count + skip-reason domain ✅

Proof run: `mania_pipeline/artifacts/runs/20260314T210035Z_s05_governance_smoke/`

## Requirements Advanced

- R010 — S05 governance outputs now provide explicit machine-readable inputs S06 artifact/regression gates can consume.
- R018 — reason-coded skip diagnostics and executed-group counters establish the failure-visibility surface needed by regression policies.

## Requirements Validated

- R008 — `governance_ledger.csv` and governance wiring contracts are runtime-validated.
- R009 — `ablation_report.json` with required delta schema and diagnostics is runtime-validated.

## New Requirements Surfaced

- none

## Requirements Invalidated or Re-scoped

- none

## Deviations

none

## Known Limitations

- Ablation retrain currently reuses training routine with verbose stdout; functional but noisy in long runs.
- Suspicious-group selection is deterministic and bounded, but threshold policy may still need tuning once S06 historical regression data accumulates.

## Follow-ups

- In S06, consume `governance.summary` counters + `ablation_report.json` as direct regression-gate inputs (don’t re-infer from raw rows).
- Version gate policy for sparse conditions (`split_empty`, `empty_high_prob_band`) explicitly.

## Files Created/Modified

- `mania_pipeline/scripts/feature_governance.py` — governance + ablation selection/delta/summary primitives.
- `mania_pipeline/scripts/run_pipeline.py` — ablation retrain integration, governance artifact/summary payload wiring.
- `mania_pipeline/tests/test_feature_governance_ledger.py` — ledger contract coverage.
- `mania_pipeline/tests/test_feature_governance_ablation.py` — ablation helper contract coverage.
- `mania_pipeline/tests/test_run_pipeline_s05_governance_contract.py` — eval-stage governance wiring (ledger + ablation).
- `.gsd/milestones/M001/slices/S05/S05-PLAN.md` — T01/T02/T03 marked complete.
- `.gsd/milestones/M001/M001-ROADMAP.md` — S05 marked complete.
- `.gsd/REQUIREMENTS.md` — R008/R009 moved to validated; coverage summary updated.
- `.gsd/PROJECT.md` — current state refreshed for S05 completion.
- `.gsd/STATE.md` — active slice/task handoff moved to S06.

## Forward Intelligence

### What the next slice should know
- Governance payload is already mirrored in both `eval_report` and `run_metadata`; S06 can gate directly on those structured fields.

### What's fragile
- Runtime cost scales with selected ablation groups; keep cap discipline and avoid accidental selection-policy drift.

### Authoritative diagnostics
- `run_metadata.json.stage_outputs.eval_report.governance.summary` is the fastest reliable decision surface; `ablation_report.json` is the detailed drill-down.

### What assumptions changed
- “Ablation likely needs a separate stage” — not required; eval-stage extension was enough and kept topology contract intact.
