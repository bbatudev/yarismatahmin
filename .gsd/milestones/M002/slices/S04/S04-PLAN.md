# S04: Policy-Gated Final Integration

**Goal:** Governance decision sinyallerini regression gate’e bağlayıp policy-aware final integration davranışını canonical artifact yüzeyinde görünür kılmak.
**Demo:** Canonical run’da `policy_gate_report.json` üretilir; regression gate fallback/warning davranışı governance decision sinyaline göre raporlanır.

## Must-Haves

- Regression gate policy fallback kuralı açık ve reason-coded olmalı.
- `policy_gate_report.json` artifact stage’de üretilmeli ve return/manifest contract’ına bağlanmalı.
- Policy fallback davranışı testle ve gerçek smoke run ile doğrulanmalı.

## Proof Level

- This slice proves: final-assembly
- Real runtime required: yes
- Human/UAT required: no

## Verification

- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_m002_s04_policy_gate_contract.py mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py mania_pipeline/tests/test_run_pipeline_s07_submission_contract.py -q`
- `./venv/Scripts/python -m pytest mania_pipeline/tests -q`
- `./venv/Scripts/python mania_pipeline/scripts/run_pipeline.py --seed 42 --run-label m002_s04_policy_gate_smoke`
- `./venv/Scripts/python -c "import json,pathlib; run=sorted(pathlib.Path('mania_pipeline/artifacts/runs').glob('*_m002_s04_policy_gate_smoke'))[-1]; md=json.loads((run/'run_metadata.json').read_text()); art=md['stage_outputs']['artifact']; pg=pathlib.Path(art['policy_gate']['report_json']); assert pg.exists(); payload=json.loads(pg.read_text()); assert set(payload['by_gender'])=={'men','women'}; print('M002/S04 policy gate contract ok:', run.name)"`

## Observability / Diagnostics

- Runtime signals: `stage_outputs.artifact.policy_gate.status`, `stage_outputs.artifact.regression_gate.status`
- Inspection surfaces: `policy_gate_report.json`, `regression_gate_report.json`, `artifact_manifest.json.contracts.policy_gate`
- Failure visibility: `blocking_failures` + `warnings` + per-gender `policy_fallback_applied`
- Redaction constraints: aggregate-only decision/gate metrics.

## Integration Closure

- Upstream surfaces consumed: S03 `governance_decision` + S04 regression snapshot extraction.
- New wiring introduced in this slice: policy-aware regression fallback + policy gate report emission.
- What remains before the milestone is truly usable end-to-end: nothing (M002 closure proof complete).

## Tasks

- [x] **T01: Add policy-aware regression gate fallback logic** `est:50m`
  - Why: S04 çekirdek hedefi decision sinyalinin gate davranışını etkilemesi.
  - Files: `mania_pipeline/scripts/run_pipeline.py`, `mania_pipeline/tests/test_run_pipeline_m002_s04_policy_gate_contract.py`
  - Do: regression gate’e fallback koşulu (`apply_calibration_policy`, confidence threshold, positive improvement) ekle; warning surface üret.
  - Verify: `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_m002_s04_policy_gate_contract.py -q`
  - Done when: calibration degradation belirli koşulda warning/fallback olur, aksi halde fail semantics korunur.

- [x] **T02: Emit policy gate integration report and wire manifest/return contracts** `est:30m`
  - Why: Final assembly için coupling diagnostics artifact gereklidir.
  - Files: `mania_pipeline/scripts/run_pipeline.py`, `mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py`, `mania_pipeline/tests/test_run_pipeline_s07_submission_contract.py`
  - Do: `policy_gate_report.json` üret; artifact manifest + stage_artifact return’a `policy_gate` bloğu ekle.
  - Verify: `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py mania_pipeline/tests/test_run_pipeline_s07_submission_contract.py -q`
  - Done when: policy gate raporu canonical artifact surfaces üzerinden izlenebilir.

- [x] **T03: Final runtime integration proof and milestone closure docs** `est:35m`
  - Why: Milestone DoD gereği gerçek canonical proof zorunlu.
  - Files: `.gsd/milestones/M002/slices/S04/S04-SUMMARY.md`, `.gsd/milestones/M002/M002-SUMMARY.md`, `mania_pipeline/artifacts/runs/<run_id>/policy_gate_report.json`
  - Do: smoke run + assert al; slice/milestone/global dokümanları tamamla.
  - Verify: `./venv/Scripts/python mania_pipeline/scripts/run_pipeline.py --seed 42 --run-label m002_s04_policy_gate_smoke`
  - Done when: policy-gated final integration kanıtı artifact ve metadata’da doğrulanır.

## Files Likely Touched

- `mania_pipeline/scripts/run_pipeline.py`
- `mania_pipeline/tests/test_run_pipeline_m002_s04_policy_gate_contract.py`
- `.gsd/milestones/M002/slices/S04/S04-SUMMARY.md`
- `.gsd/milestones/M002/M002-SUMMARY.md`
