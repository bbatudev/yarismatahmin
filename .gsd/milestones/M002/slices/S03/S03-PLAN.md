# S03: Governance Decision Fusion (Ablation + Drift + Calibration)

**Goal:** Ablation, drift ve calibration policy sinyallerini tek governance decision contract’ında birleştirmek.
**Demo:** Canonical run `governance_decision_report.json` üretir; `eval_report.json` ve `run_metadata.json.stage_outputs.eval_report.governance_decision` mirror payload taşır.

## Must-Haves

- Gender bazında `decision`, `confidence`, `reason_codes`, `evidence_bundle` alanları üretilir.
- Aggregate karar (`review_feature_groups|enforce_calibration_policy|monitor_drift|hold_baseline`) persist edilir.
- Artifact contract `governance_decision_report_json` dosyasını required listede doğrular.

## Proof Level

- This slice proves: integration
- Real runtime required: yes
- Human/UAT required: no

## Verification

- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_m002_s03_governance_decision_contract.py mania_pipeline/tests/test_run_pipeline_s05_governance_contract.py mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py mania_pipeline/tests/test_run_pipeline_s07_submission_contract.py -q`
- `./venv/Scripts/python -m pytest mania_pipeline/tests -q`
- `./venv/Scripts/python mania_pipeline/scripts/run_pipeline.py --seed 42 --run-label m002_s03_decision_smoke`
- `./venv/Scripts/python -c "import json,pathlib; run=sorted(pathlib.Path('mania_pipeline/artifacts/runs').glob('*_m002_s03_decision_smoke'))[-1]; md=json.loads((run/'run_metadata.json').read_text()); gd=md['stage_outputs']['eval_report']['governance_decision']; rpt=pathlib.Path(gd['report_json']); assert rpt.exists(); data=json.loads(rpt.read_text()); assert set(data['by_gender'])=={'men','women'}; print('M002/S03 governance decision contract ok:', run.name)"`

## Observability / Diagnostics

- Runtime signals: `stage_outputs.eval_report.governance_decision.by_gender.<gender>.decision`
- Inspection surfaces: `governance_decision_report.json`, `eval_report.json.governance_decision`, `run_metadata.json.stage_outputs.eval_report.governance_decision`
- Failure visibility: reason codes + evidence bundle (`ablation`, `drift`, `calibration_policy`) same payload içinde.
- Redaction constraints: only aggregate evidence; no row-level data persisted.

## Integration Closure

- Upstream surfaces consumed: S01 drift payload, S02 calibration policy payload, S05 ablation outputs.
- New wiring introduced in this slice: governance decision report emission + artifact required surface expansion.
- What remains before the milestone is truly usable end-to-end: S04 policy-gated final integration.

## Tasks

- [x] **T01: Add governance decision fusion helpers and report generation** `est:45m`
  - Why: Multi-evidence karar için deterministic fusion katmanı gerekiyor.
  - Files: `mania_pipeline/scripts/run_pipeline.py`, `mania_pipeline/tests/test_run_pipeline_m002_s03_governance_decision_contract.py`
  - Do: gender-level decision helper’ları yaz; aggregate decision üret; report artifact persist et.
  - Verify: `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_m002_s03_governance_decision_contract.py -q`
  - Done when: governance decision payload reason-coded evidence bundle ile üretilir.

- [x] **T02: Wire governance decision into eval output and artifact contract** `est:35m`
  - Why: S03 demo contract mirror + required artifact enforce gerektiriyor.
  - Files: `mania_pipeline/scripts/run_pipeline.py`, `mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py`, `mania_pipeline/tests/test_run_pipeline_s07_submission_contract.py`
  - Do: eval return/report’a `governance_decision` ekle; artifact required list’e `governance_decision_report_json` ekle; fixture’ları güncelle.
  - Verify: `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py mania_pipeline/tests/test_run_pipeline_s07_submission_contract.py -q`
  - Done when: artifact stage yeni decision report path’ını fail-fast doğrular.

- [x] **T03: Runtime proof and S03 closure docs** `est:30m`
  - Why: S03 entegrasyonunun canlı canonical run kanıtı gerekli.
  - Files: `.gsd/milestones/M002/slices/S03/S03-SUMMARY.md`, `.gsd/milestones/M002/slices/S03/tasks/T03-SUMMARY.md`, `mania_pipeline/artifacts/runs/<run_id>/governance_decision_report.json`
  - Do: smoke run + metadata assert al; task/slice/global docs güncelle.
  - Verify: `./venv/Scripts/python mania_pipeline/scripts/run_pipeline.py --seed 42 --run-label m002_s03_decision_smoke`
  - Done when: governance decision artifact/payload runtime’da doğrulanır.

## Files Likely Touched

- `mania_pipeline/scripts/run_pipeline.py`
- `mania_pipeline/tests/test_run_pipeline_m002_s03_governance_decision_contract.py`
- `mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py`
- `mania_pipeline/tests/test_run_pipeline_s07_submission_contract.py`
