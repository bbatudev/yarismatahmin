---
id: M002
provides:
  - Drift-to-policy-to-governance-to-gate integration contract for probability quality control in canonical runs.
key_decisions:
  - Keep all M002 capabilities inside existing canonical stages and extend eval/artifact payload contracts instead of adding stages.
patterns_established:
  - Every new control-plane report is machine-readable, mirrored in run metadata, and verified by both tests and runtime smoke proof.
observability_surfaces:
  - drift_regime_report.json
  - calibration_policy_report.json
  - governance_decision_report.json
  - policy_gate_report.json
requirement_outcomes:
  - id: R014
    from_status: active
    to_status: validated
    proof: S02 policy contract tests + canonical smoke (`m002_s02_policy_smoke`) and persisted `calibration_policy_report.json`.
duration: ~1d
verification_result: passed
completed_at: 2026-03-15
---

# M002: Probability Quality & Governance

**M002 delivered a full control-plane chain from drift sensing to policy selection, governance fusion, and policy-gated regression behavior in canonical runs.**

## What Happened

M002 progressed in four slices with a stable stage topology:
- **S01** added regime drift signals (`drift_regime_report.json`) and payload mirrors.
- **S02** added deterministic regime-aware calibration policy selection (`calibration_policy_report.json`).
- **S03** fused ablation + drift + policy evidence into governance decisions (`governance_decision_report.json`).
- **S04** coupled governance policy signals into regression gate behavior and emitted final integration diagnostics (`policy_gate_report.json`).

Across slices, the key architectural pattern was consistent: compute in eval/artifact seams, persist machine-readable reports, mirror into `run_metadata`, and lock behavior with contract tests plus real smoke runs.

## Cross-Slice Verification

- Slice contract tests for S01/S02/S03/S04 all passed.
- Full suite verification after S04: `./venv/Scripts/python -m pytest mania_pipeline/tests -q` → **47 passed**.
- Canonical smoke proofs executed and asserted:
  - `m002_s01_drift_smoke`
  - `m002_s02_policy_smoke`
  - `m002_s03_decision_smoke`
  - `m002_s04_policy_gate_smoke`
- Final policy-gate artifact and metadata mirror verified from runtime outputs.

## Requirement Changes

- R014: active → validated — S02 contract + runtime proof produced deterministic calibration policy output surface.

## Forward Intelligence

### What the next milestone should know
- M002 leaves a complete machine-readable decision chain; M003 can optimize/tune thresholds and model strategy without redesigning control surfaces.

### What's fragile
- Confidence and threshold constants in S02/S04 are first-pass heuristics; they are functional but likely need data-driven tuning.

### Authoritative diagnostics
- For policy behavior: read `policy_gate_report.json` + `regression_gate_report.json` together.
- For upstream evidence: `governance_decision_report.json` then `calibration_policy_report.json` then `drift_regime_report.json`.

### What assumptions changed
- Initial assumption that regression calibration degradation must always hard-fail changed to policy-conditioned fallback with explicit warnings.

## Files Created/Modified

- `mania_pipeline/scripts/run_pipeline.py` — M002 control-plane integration across S01-S04.
- `mania_pipeline/tests/test_run_pipeline_m002_s01_drift_contract.py` — S01 contract.
- `mania_pipeline/tests/test_run_pipeline_m002_s02_calibration_policy_contract.py` — S02 contract.
- `mania_pipeline/tests/test_run_pipeline_m002_s03_governance_decision_contract.py` — S03 contract.
- `mania_pipeline/tests/test_run_pipeline_m002_s04_policy_gate_contract.py` — S04 contract.
- `.gsd/milestones/M002/M002-SUMMARY.md` — milestone closure record.
