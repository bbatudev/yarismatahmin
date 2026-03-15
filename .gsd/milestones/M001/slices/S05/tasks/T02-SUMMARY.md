---
id: T02
parent: S05
milestone: M001
provides:
  - Deterministic controlled-ablation retrain flow with split-aware delta schema and bounded suspicious-group selection.
key_files:
  - mania_pipeline/scripts/feature_governance.py
  - mania_pipeline/scripts/run_pipeline.py
  - mania_pipeline/tests/test_feature_governance_ablation.py
  - mania_pipeline/tests/test_run_pipeline_s05_governance_contract.py
key_decisions:
  - D021: deterministic + capped suspicious-group subset retrain policy.
patterns_established:
  - Governance module owns selection/delta/summary primitives; orchestrator owns runtime loading/retrain/artifact emission.
observability_surfaces:
  - run_metadata.json.stage_outputs.eval_report.governance.summary.{selected_group_count,executed_group_count,skipped_groups}
  - ablation_report.json
duration: ~1h 35m
verification_result: passed
completed_at: 2026-03-15
blocker_discovered: false
---

# T02: Implement controlled ablation retrain and delta report schema

**Added controlled group ablation retraining and emitted machine-readable Val/Test delta evidence (Brier/LogLoss/AUC + calibration deltas) with deterministic selection and bounded runtime.**

## What Happened

- Extended `feature_governance.py` with T02 primitives:
  - `select_suspicious_groups(...)` (deterministic, capped ordering),
  - `build_group_gender_feature_map(...)`,
  - `compute_ablation_split_deltas(...)` (Val/Test delta schema),
  - `build_ablation_summary(...)`,
  - skip-reason domain normalization (`group_missing`, `no_gender_features`, `split_empty`, `empty_high_prob_band`).
- Extended `run_pipeline.py::stage_eval_report`:
  - keeps baseline calibration/governance flow,
  - runs per-group/per-gender column-drop retrain via `train_baseline(..., random_state=seed)`,
  - computes split-level ablation deltas against baseline metrics + calibration summaries,
  - writes `ablation_report.json`,
  - exposes governance summary counters and skip diagnostics in stage output.
- Updated S05 governance contract test to assert ablation artifact and summary surfaces.
- Replaced T02 xfail scaffold with concrete unit tests for selection determinism, delta schema, and summary reason-domain enforcement.

## Verification

- ✅ `./venv/Scripts/python -m pytest mania_pipeline/tests/test_feature_governance_ablation.py`
- ✅ `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_s05_governance_contract.py -k ablation`
- ✅ `./venv/Scripts/python -m pytest mania_pipeline/tests/test_feature_governance_ablation.py mania_pipeline/tests/test_run_pipeline_s05_governance_contract.py -q`

## Diagnostics

- Inspect `mania_pipeline/artifacts/runs/<run_id>/ablation_report.json` for group-level execution status and split deltas.
- Inspect `mania_pipeline/artifacts/runs/<run_id>/run_metadata.json` → `stage_outputs.eval_report.governance.summary` for aggregate counters and skip reasons.
- Skip reasons are normalized to the explicit domain, so downstream regression gates can parse deterministically.

## Deviations

- None.

## Known Issues

- Ablation retrain currently logs full LightGBM training output during eval stage, which is noisy but functional.

## Files Created/Modified

- `mania_pipeline/scripts/feature_governance.py` — ablation selection/delta/summary helpers + reason normalization.
- `mania_pipeline/scripts/run_pipeline.py` — controlled ablation retrain flow + `ablation_report.json` emission + governance summary counters.
- `mania_pipeline/tests/test_feature_governance_ablation.py` — concrete T02 contract tests.
- `mania_pipeline/tests/test_run_pipeline_s05_governance_contract.py` — ablation artifact + summary wiring assertions.
- `.gsd/milestones/M001/slices/S05/S05-PLAN.md` — marked T02 completed.
