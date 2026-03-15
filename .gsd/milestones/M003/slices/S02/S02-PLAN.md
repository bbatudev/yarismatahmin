# S02: Reproducible HPO Search Harness

**Goal:** Canonical train stage’de deterministic HPO deneme/raporlama katmanı kurmak.
**Demo:** `--hpo-trials > 0` ile run alındığında `hpo_report.json` üretilir ve `stage_outputs.train.hpo` altında gender bazlı best-trial sinyali görünür.

## Must-Haves

- CLI: `--hpo-trials`, `--hpo-target-profile` desteklenir.
- Deterministic trial param üretimi (seed’e bağlı).
- `hpo_report.json` her run’da (gerekirse skipped) persist edilir.

## Proof Level

- This slice proves: integration
- Real runtime required: yes
- Human/UAT required: no

## Verification

- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_m003_s02_hpo_contract.py mania_pipeline/tests/test_run_pipeline_m003_s01_training_profile_contract.py mania_pipeline/tests/test_run_pipeline_cli.py mania_pipeline/tests/test_run_pipeline_s03_eval_contract.py -q`
- `./venv/Scripts/python -m pytest mania_pipeline/tests -q`
- `./venv/Scripts/python mania_pipeline/scripts/run_pipeline.py --seed 42 --training-profile quality_v1 --hpo-trials 2 --hpo-target-profile quality_v1 --run-label m003_s02_hpo_smoke --artifacts-root mania_pipeline/artifacts/runs_m003`
- `./venv/Scripts/python -c "import json,pathlib; run=sorted(pathlib.Path('mania_pipeline/artifacts/runs_m003').glob('*_m003_s02_hpo_smoke'))[-1]; md=json.loads((run/'run_metadata.json').read_text()); hpo=md['stage_outputs']['train']['hpo']; rpt=pathlib.Path(hpo['report_json']); assert rpt.exists(); data=json.loads(rpt.read_text()); assert set(data['by_gender'])=={'men','women'}; print('M003/S02 HPO contract ok:', run.name)"`

## Observability / Diagnostics

- Runtime signals: `stage_outputs.train.hpo.status`, `best_trial_id`, `best_val_brier`
- Inspection surfaces: `hpo_report.json`, `run_metadata.json.stage_outputs.train.hpo`
- Failure visibility: per-trial `status/reason` ve `no_successful_trials` reason.
- Redaction constraints: aggregate metric + param only, row-level prediction yok.

## Integration Closure

- Upstream surfaces consumed: S01 training-profile seam.
- New wiring introduced in this slice: train-stage HPO harness/report emission.
- What remains before the milestone is truly usable end-to-end: S03 ensemble integration + S04 readiness gate.

## Tasks

- [x] **T01: Add HPO trial generation and train invocation compatibility** `est:45m`
  - Why: Deterministic search için trial param ve train çağrı katmanı gerekli.
  - Files: `mania_pipeline/scripts/run_pipeline.py`, `mania_pipeline/scripts/03_lgbm_train.py`
  - Do: param override destekli trainer çağrısı, deterministic trial builder ve per-gender search loop ekle.
  - Verify: `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_m003_s02_hpo_contract.py -k "reproducible" -q`
  - Done when: aynı seed ile aynı trial param dizisi üretiliyor.

- [x] **T02: Emit hpo_report artifact and wire into train payload/CLI** `est:35m`
  - Why: S02 demo koşulu machine-readable report ve metadata mirror gerektiriyor.
  - Files: `mania_pipeline/scripts/run_pipeline.py`, `mania_pipeline/tests/test_run_pipeline_m003_s02_hpo_contract.py`
  - Do: CLI arglarını ekle, train output’a `hpo` bloğu yaz, report dosyasını persist et.
  - Verify: `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_m003_s02_hpo_contract.py -q`
  - Done when: hpo report path + best trial sinyali train payload’da görünür.

- [x] **T03: Runtime proof and S02 closure docs** `est:30m`
  - Why: gerçek canonical run ile HPO contract kapanışı gerekli.
  - Files: `.gsd/milestones/M003/slices/S02/S02-SUMMARY.md`, `.gsd/milestones/M003/slices/S02/tasks/T03-SUMMARY.md`, `mania_pipeline/artifacts/runs_m003/<run_id>/hpo_report.json`
  - Do: hpo smoke run, post-run assert, docs closure.
  - Verify: `./venv/Scripts/python mania_pipeline/scripts/run_pipeline.py --seed 42 --training-profile quality_v1 --hpo-trials 2 --hpo-target-profile quality_v1 --run-label m003_s02_hpo_smoke --artifacts-root mania_pipeline/artifacts/runs_m003`
  - Done when: runtime’da hpo artifact/payload doğrulanır.

## Files Likely Touched

- `mania_pipeline/scripts/03_lgbm_train.py`
- `mania_pipeline/scripts/run_pipeline.py`
- `mania_pipeline/tests/test_run_pipeline_m003_s02_hpo_contract.py`
