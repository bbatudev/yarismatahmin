---
id: M001
provides:
  - End-to-end canonical foundation with leakage-safe feature/train/eval, calibration+governance, artifact contracts, regression/repro gates, and optional submission validation.
key_decisions:
  - D001/D019: script-first single execution path with topology lock.
  - D005/D024: regression+artifact enforcement as machine-readable, blocking policy gates.
  - D026: strict `ID,Pred` submission validation as fail-fast contract.
patterns_established:
  - Eval-stage extension for quality/governance outputs without stage explosion.
  - Artifact-stage report-first + fail-fast enforcement for operational gates.
observability_surfaces:
  - run_metadata.json + stage_events.jsonl
  - eval_report.json (`metrics_table`, `calibration`, `governance`)
  - artifact contract/gate reports (`artifact_contract_report.json`, `reproducibility_report.json`, `regression_gate_report.json`, `submission_validation_report.json`)
requirement_outcomes:
  - id: R008
    from_status: active
    to_status: validated
    proof: S05 governance ledger contract tests + canonical smoke run artifacts
  - id: R009
    from_status: active
    to_status: validated
    proof: S05 ablation delta contract tests + runtime assertions
  - id: R010
    from_status: active
    to_status: validated
    proof: S06 artifact contract report + required-file fail-fast enforcement
  - id: R011
    from_status: active
    to_status: validated
    proof: S06 reproducibility gate pass/fail checks on same commit+seed runs
  - id: R018
    from_status: active
    to_status: validated
    proof: S06 regression gate report policy enforcement + tests
  - id: R012
    from_status: active
    to_status: validated
    proof: S07 submission-enabled canonical runtime and strict `ID,Pred` validation report
duration: 2026-03-14 → 2026-03-15
verification_result: passed
completed_at: 2026-03-15
---

# M001: Canonical Foundation

**M001 delivered a single authoritative pipeline that is leakage-safe, reproducible, policy-gated, and submission-ready at contract level.**

## What Happened

M001 progressively hardened the pipeline from “works end-to-end” to “operationally trustworthy.”

- S01/S02 established canonical orchestration and fail-fast split/leakage safety.
- S03 unified Men/Women training/eval contracts and technically enforced script-only training authority.
- S04 added calibration artifacts and overconfidence diagnostics as canonical eval outputs.
- S05 added feature governance ledger + controlled ablation deltas with deterministic diagnostics.
- S06 added artifact contract enforcement, reproducibility tolerance gate, and previous-run regression gate.
- S07 completed optional submission generation/validation and final integration proof.

The result is a single command path with machine-readable outputs for both quality and failure states.

## Cross-Slice Verification

- Full test suite: `./venv/Scripts/python -m pytest mania_pipeline/tests -q` ✅
- Canonical runtime proof sequence:
  - `--run-label s05_governance_smoke` ✅
  - `--run-label s06_contract_smoke` ✅
  - `--run-label s06_repro_check` ✅ (repro gate pass)
  - `--run-label s07_submission_smoke --submission-stage stage2` ✅ (submission contract pass)
- Artifact/run assertions validated:
  - calibration/governance artifacts present and wired
  - artifact/repro/regression reports present and status-valid
  - submission file schema `ID,Pred` and `Pred` range `[0,1]`

## Requirement Changes

- R008: active → validated — S05 governance ledger contract and runtime evidence.
- R009: active → validated — S05 ablation report schema and runtime diagnostics.
- R010: active → validated — S06 artifact contract report + fail-fast enforcement.
- R011: active → validated — S06 reproducibility tolerance gate with runtime pass evidence.
- R018: active → validated — S06 regression gate policy report + enforcement.
- R012: active → validated — S07 submission generation and strict validation in runtime.

## Forward Intelligence

### What the next milestone should know
- M002 can build directly on stable machine-readable surfaces; avoid re-deriving signals from raw logs.

### What's fragile
- Regression/repro baselines depend on prior run history hygiene — accidental run deletion can change comparisons.

### Authoritative diagnostics
- `run_metadata.json.stage_outputs` is the canonical control-plane surface; per-report JSON files provide drill-down truth.

### What assumptions changed
- “Quality gates need extra stages” — false; keeping gates in eval/artifact stages preserved topology while still enforcing contracts.

## Files Created/Modified

- `mania_pipeline/scripts/run_pipeline.py` — canonical orchestration + all gate/report integrations.
- `mania_pipeline/scripts/feature_governance.py` — governance and controlled ablation primitives.
- `mania_pipeline/tests/test_run_pipeline_s04_calibration_contract.py` — calibration contract coverage.
- `mania_pipeline/tests/test_run_pipeline_s05_governance_contract.py` — governance contract coverage.
- `mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py` — S06 gate contract coverage.
- `mania_pipeline/tests/test_run_pipeline_s07_submission_contract.py` — submission contract coverage.
- `.gsd/REQUIREMENTS.md` — requirement status transitions to validated.
- `.gsd/milestones/M001/M001-ROADMAP.md` — all slices completed.
