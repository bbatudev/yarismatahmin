---
id: T03
parent: S06
milestone: M001
provides:
  - Previous-run regression gate report with blocking/non-blocking rule separation and manifest/metadata wiring.
key_files:
  - mania_pipeline/scripts/run_pipeline.py
  - mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py
key_decisions:
  - D005: Brier mandatory, calibration degradation fail, AUC informational policy is enforced as gate logic.
patterns_established:
  - Gate report pattern: explicit blocking_failures + per-gender rule payloads.
observability_surfaces:
  - regression_gate_report.json
  - artifact_manifest.json.contracts.regression_gate
  - stage_outputs.artifact.regression_gate.status
duration: ~45m
verification_result: passed
completed_at: 2026-03-15
blocker_discovered: false
---

# T03: Implement previous-run regression gate and wire statuses into manifest/metadata

**Added previous-run regression gate with multi-rule policy and wired statuses to manifest + stage outputs.**

## What Happened

- Previous successful run baseline lookup (latest succeeded run) stage_artifact’e bağlandı.
- Regression evaluator eklendi:
  - Brier: mandatory non-degradation (blocking)
  - Calibration: degradation fail (blocking; ece/wmae/high-prob abs gap)
  - AUC: informational
- `regression_gate_report.json` yazımı eklendi.
- Manifest `contracts` bloğu ve `stage_outputs.artifact` status/path yüzeyleri tamamlandı.
- Blocking failure’da stage fail semantics eklendi.

## Verification

- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py -k "regression"` ✅
- `./venv/Scripts/python mania_pipeline/scripts/run_pipeline.py --seed 42 --run-label s06_contract_smoke` ✅
- run assert: `regression_gate_report.json.status in {'passed','skipped'}` ve contract artifacts mevcut ✅

## Diagnostics

- `mania_pipeline/artifacts/runs/<run_id>/regression_gate_report.json`
- `artifact_manifest.json -> contracts.regression_gate`
- `run_metadata.json -> stage_outputs.artifact.regression_gate`

## Deviations

none

## Known Issues

none

## Files Created/Modified

- `mania_pipeline/scripts/run_pipeline.py` — regression gate evaluator + wiring.
- `mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py` — regression policy assertions.
