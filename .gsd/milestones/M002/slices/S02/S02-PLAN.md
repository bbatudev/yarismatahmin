# S02: Regime-Aware Calibration Policy Engine

**Goal:** Drift rejim sinyalini consume eden deterministik calibration method selector’ını canonical eval flow’a eklemek.
**Demo:** `run_pipeline.py` çalışınca `calibration_policy_report.json` üretilir; `eval_report.json` ve `run_metadata.json.stage_outputs.eval_report.calibration_policy` aynı policy payload’ını taşır.

## Must-Haves

- Policy engine aday yöntemleri (`none`, `platt`, `isotonic`) Val/Test metrikleriyle raporlar.
- Seçim deterministik olur; low-sample/single-class durumları reason-coded unavailable olarak persist edilir.
- Artifact stage `calibration_policy_report_json` dosyasını zorunlu artifact contract’a dahil eder.

## Proof Level

- This slice proves: integration
- Real runtime required: yes
- Human/UAT required: no

## Verification

- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_m002_s02_calibration_policy_contract.py mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py mania_pipeline/tests/test_run_pipeline_s07_submission_contract.py -q`
- `./venv/Scripts/python -m pytest mania_pipeline/tests -q`
- `./venv/Scripts/python mania_pipeline/scripts/run_pipeline.py --seed 42 --run-label m002_s02_policy_smoke`
- `./venv/Scripts/python -c "import json,pathlib; run=sorted(pathlib.Path('mania_pipeline/artifacts/runs').glob('*_m002_s02_policy_smoke'))[-1]; md=json.loads((run/'run_metadata.json').read_text()); p=md['stage_outputs']['eval_report']['calibration_policy']; rpt=pathlib.Path(p['report_json']); assert rpt.exists(); data=json.loads(rpt.read_text()); assert set(data['by_gender'])=={'men','women'}; assert all(data['by_gender'][g]['selected_method'] in {'none','platt','isotonic'} for g in ('men','women')); print('M002/S02 policy contract ok:', run.name)"`

## Observability / Diagnostics

- Runtime signals: `stage_outputs.eval_report.calibration_policy.by_gender.<gender>.selected_method`
- Inspection surfaces: `calibration_policy_report.json`, `eval_report.json.calibration_policy`, `run_metadata.json.stage_outputs.eval_report.calibration_policy`
- Failure visibility: `candidate_methods.<method>.status/reason`, `selection_reason`, `drift_alert_codes`
- Redaction constraints: aggregate-only; no row-level prediction dump.

## Integration Closure

- Upstream surfaces consumed: S01 drift payload (`drift.by_gender`, `drift.alerts`) + eval split probabilities.
- New wiring introduced in this slice: policy report emission + artifact contract required path update.
- What remains before the milestone is truly usable end-to-end: S03 governance decision fusion ve S04 policy-gated final integration.

## Tasks

- [x] **T01: Implement deterministic regime-aware calibration selector helpers** `est:50m`
  - Why: Policy kararı test edilebilir ve reason-coded olmak zorunda.
  - Files: `mania_pipeline/scripts/run_pipeline.py`, `mania_pipeline/tests/test_run_pipeline_m002_s02_calibration_policy_contract.py`
  - Do: availability gates (min sample, single class), candidate scoring, regime-based method order ve deterministic selection reason üret.
  - Verify: `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_m002_s02_calibration_policy_contract.py -k "small|policy" -q`
  - Done when: helper’lar `selected_method` + `candidate_methods` + reason alanlarını stabil üretir.

- [x] **T02: Emit calibration policy artifact and update artifact contract fixtures** `est:40m`
  - Why: S02 demo koşulu artifact+persistent wiring gerektiriyor.
  - Files: `mania_pipeline/scripts/run_pipeline.py`, `mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py`, `mania_pipeline/tests/test_run_pipeline_s07_submission_contract.py`
  - Do: `calibration_policy_report.json` üret; eval payload’a bağla; S06 artifact required list ve fixture’ları senkronize et.
  - Verify: `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py mania_pipeline/tests/test_run_pipeline_s07_submission_contract.py -q`
  - Done when: artifact stage yeni policy report path’ını required olarak doğrular.

- [x] **T03: Prove runtime policy contract and close S02 docs** `est:30m`
  - Why: Milestone doğruluğu için gerçek canonical run kanıtı gerekiyor.
  - Files: `.gsd/milestones/M002/slices/S02/S02-SUMMARY.md`, `.gsd/milestones/M002/slices/S02/tasks/T03-SUMMARY.md`, `mania_pipeline/artifacts/runs/<run_id>/calibration_policy_report.json`
  - Do: smoke run al, post-run assert ile policy surface’i doğrula, task/slice summary yaz.
  - Verify: `./venv/Scripts/python mania_pipeline/scripts/run_pipeline.py --seed 42 --run-label m002_s02_policy_smoke`
  - Done when: runtime’da policy artifact/payload mirror doğrulanır.

## Files Likely Touched

- `mania_pipeline/scripts/run_pipeline.py`
- `mania_pipeline/tests/test_run_pipeline_m002_s02_calibration_policy_contract.py`
- `mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py`
- `mania_pipeline/tests/test_run_pipeline_s07_submission_contract.py`
