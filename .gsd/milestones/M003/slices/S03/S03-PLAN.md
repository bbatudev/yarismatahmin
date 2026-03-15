# S03: Ensemble Candidate Integration

**Goal:** Baseline vs HPO/weighted-ensemble adaylarını canonical eval stage’de karşılaştırıp seçim sinyalini machine-readable olarak yayınlamak.
**Demo:** `stage_eval_report` sonunda `ensemble_report.json` üretilir ve `stage_outputs.eval_report.ensemble` altında selected candidate + aggregate decision görünür.

## Must-Haves

- `ensemble_report.json` her eval run’ında üretilir.
- `eval_report.json.ensemble` ve metadata mirror (`stage_outputs.eval_report.ensemble`) bağlıdır.

## Proof Level

- This slice proves: integration
- Real runtime required: yes
- Human/UAT required: no

## Verification

- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_m003_s03_ensemble_contract.py mania_pipeline/tests/test_run_pipeline_s03_eval_contract.py mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py mania_pipeline/tests/test_run_pipeline_s07_submission_contract.py mania_pipeline/tests/test_run_pipeline_m002_s04_policy_gate_contract.py mania_pipeline/tests/test_run_pipeline_m003_s02_hpo_contract.py -q`
- `./venv/Scripts/python -m pytest mania_pipeline/tests -q`
- `./venv/Scripts/python mania_pipeline/scripts/run_pipeline.py --seed 42 --training-profile quality_v1 --hpo-trials 2 --hpo-target-profile quality_v1 --run-label m003_s03_ensemble_smoke --artifacts-root mania_pipeline/artifacts/runs_m003`
- `./venv/Scripts/python -c "import json,pathlib; run=sorted(pathlib.Path('mania_pipeline/artifacts/runs_m003').glob('*_m003_s03_ensemble_smoke'))[-1]; md=json.loads((run/'run_metadata.json').read_text()); ens=md['stage_outputs']['eval_report']['ensemble']; rpt=pathlib.Path(ens['report_json']); assert rpt.exists(); data=json.loads(rpt.read_text()); assert set(data['by_gender'])=={'men','women'}; print('S03 ensemble ok', data['aggregate']['decision'])"`

## Observability / Diagnostics

- Runtime signals: `stage_outputs.eval_report.ensemble.by_gender.<gender>.selected_candidate_id`
- Inspection surfaces: `ensemble_report.json`, `eval_report.json.ensemble`
- Failure visibility: candidate-level `status/reason` (`hpo_retrain_failed`, `probability_shape_mismatch`, `no_available_candidates`)
- Redaction constraints: yalnızca aggregate metrics/params; row-level prediction persist edilmez.

## Integration Closure

- Upstream surfaces consumed: S02 `hpo_report.json` + baseline eval probability seams.
- New wiring introduced in this slice: eval-stage ensemble candidate scoring/selection + artifact contract surface.
- What remains before the milestone is truly usable end-to-end: S04 submission readiness final gate.

## Tasks

- [x] **T01: Add deterministic ensemble candidate scoring in eval stage** `est:50m`
  - Why: S03’ün çekirdeği baseline/hpo/blend adaylarının tek kontratta kıyaslanması.
  - Files: `mania_pipeline/scripts/run_pipeline.py`
  - Do: helper fonksiyonlarla candidate scoring, weight search, selection threshold ve aggregate decision üret.
  - Verify: `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_m003_s03_ensemble_contract.py -q`
  - Done when: `ensemble_report.json` içinde candidate ledger + selected candidate görünür.

- [x] **T02: Wire ensemble payload into eval/artifact contracts and tests** `est:35m`
  - Why: S03 çıktısının canonical artifact contract içinde zorunlu yüzey olması gerekiyor.
  - Files: `mania_pipeline/scripts/run_pipeline.py`, `mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py`, `mania_pipeline/tests/test_run_pipeline_s07_submission_contract.py`, `mania_pipeline/tests/test_run_pipeline_m002_s04_policy_gate_contract.py`
  - Do: `eval_report` return/report wiring ve artifact required path listesine `ensemble_report_json` ekle; fixture’ları güncelle.
  - Verify: `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py mania_pipeline/tests/test_run_pipeline_s07_submission_contract.py mania_pipeline/tests/test_run_pipeline_m002_s04_policy_gate_contract.py -q`
  - Done when: artifact stage ensemble report yoksa fail edecek kontrata sahip.

- [x] **T03: Runtime proof and S03 closure artifacts** `est:30m`
  - Why: gerçek canonical run’da ensemble surface’in üretildiği kanıtlanmalı.
  - Files: `.gsd/milestones/M003/slices/S03/S03-SUMMARY.md`, `.gsd/milestones/M003/slices/S03/tasks/T03-SUMMARY.md`
  - Do: hpo-enabled smoke run + metadata assert + docs closure.
  - Verify: `./venv/Scripts/python mania_pipeline/scripts/run_pipeline.py --seed 42 --training-profile quality_v1 --hpo-trials 2 --hpo-target-profile quality_v1 --run-label m003_s03_ensemble_smoke --artifacts-root mania_pipeline/artifacts/runs_m003`
  - Done when: `stage_outputs.eval_report.ensemble` + `ensemble_report.json` runtime’da doğrulanır.

## Files Likely Touched

- `mania_pipeline/scripts/run_pipeline.py`
- `mania_pipeline/tests/test_run_pipeline_m003_s03_ensemble_contract.py`
- `mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py`
- `mania_pipeline/tests/test_run_pipeline_s07_submission_contract.py`
- `mania_pipeline/tests/test_run_pipeline_m002_s04_policy_gate_contract.py`
