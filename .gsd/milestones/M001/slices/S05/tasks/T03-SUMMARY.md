---
id: T03
parent: S05
milestone: M001
provides:
  - Canonical eval-surface governance wiring with artifact mirrors in eval_report + run_metadata and runtime contract proof.
key_files:
  - mania_pipeline/scripts/run_pipeline.py
  - mania_pipeline/tests/test_run_pipeline_s05_governance_contract.py
  - .gsd/milestones/M001/slices/S05/S05-PLAN.md
  - .gsd/DECISIONS.md
key_decisions:
  - D023: normalize skip-reason domain and lock governance summary counters under stage_outputs.eval_report.governance.summary.
patterns_established:
  - Eval-stage extension pattern preserved: new governance fields added without stage topology changes.
observability_surfaces:
  - eval_report.json.governance
  - run_metadata.json.stage_outputs.eval_report.governance
  - stage_events.jsonl + smoke-run contract assertions
duration: ~45m
verification_result: passed
completed_at: 2026-03-15
blocker_discovered: false
---

# T03: Wire governance artifacts into eval report + metadata and prove runtime contract

**Completed governance runtime wiring proof: canonical run now emits ledger+ablation artifact paths and summary/diagnostics in both eval report and stage outputs, while keeping stage order unchanged.**

## What Happened

- Finalized governance payload contract in `stage_eval_report`:
  - `artifacts.ledger_csv`
  - `artifacts.ablation_report_json`
  - `summary` with `selected_group_count`, `executed_group_count`, `skipped_groups` and existing action/group counts
  - `diagnostics.selected_groups`
- Kept canonical topology untouched (`feature`, `train`, `eval_report`, `artifact`).
- Added decision record `D023` for reason-domain + summary wiring contract.
- Marked S05 tasks `T02` and `T03` as complete in slice plan.

## Verification

- ✅ `./venv/Scripts/python -m pytest mania_pipeline/tests/test_feature_governance_ledger.py mania_pipeline/tests/test_feature_governance_ablation.py mania_pipeline/tests/test_run_pipeline_s05_governance_contract.py mania_pipeline/tests/test_run_pipeline_cli.py mania_pipeline/tests/test_run_pipeline_s04_calibration_contract.py -q`
- ✅ `./venv/Scripts/python mania_pipeline/scripts/run_pipeline.py --seed 42 --run-label s05_governance_smoke`
- ✅ `./venv/Scripts/python -c "... assert gov['artifacts']['ledger_csv'] exists ... assert gov['artifacts']['ablation_report_json'] exists ... assert executed_group_count >= 1 ..."`
- ✅ `./venv/Scripts/python -c "... assert skipped_groups reason domain subset ..."`

## Diagnostics

- Canonical proof run: `mania_pipeline/artifacts/runs/20260314T210035Z_s05_governance_smoke/`
- Inspect:
  - `eval_report.json` → `governance`
  - `run_metadata.json` → `stage_outputs.eval_report.governance`
  - `ablation_report.json`
  - `governance_ledger.csv`

## Deviations

- None.

## Known Issues

- None blocking S05 runtime contract.

## Files Created/Modified

- `mania_pipeline/scripts/run_pipeline.py` — governance payload final wiring and contract surfaces.
- `mania_pipeline/tests/test_run_pipeline_s05_governance_contract.py` — eval-report governance contract coverage (ledger + ablation).
- `.gsd/milestones/M001/slices/S05/S05-PLAN.md` — marked T03 completed.
- `.gsd/DECISIONS.md` — appended D023.
- `.gsd/milestones/M001/slices/S05/tasks/T03-SUMMARY.md` — task completion record.
