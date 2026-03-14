# S01: Regime Drift Baseline & Signal Contract

**Goal:** Canonical eval katmanında split+regime drift sinyallerini machine-readable rapora bağlamak.
**Demo:** `run_pipeline.py` çalışınca `drift_regime_report.json` üretilir; `eval_report.json` ve `run_metadata.json.stage_outputs.eval_report.drift` aynı payload’ı taşır.

## Must-Haves

- Drift report split bazında `sample_count`, `pred_mean`, `actual_rate`, `gap` alanlarını üretir.
- Test split için `close|medium|wide` regime segment summary üretilir (`SeedNum_diff` tabanlı).
- Alert listesi en az `test_gap_shift` ve `low_sample_regime` reason code’larını kapsar.

## Proof Level

- This slice proves: integration
- Real runtime required: yes
- Human/UAT required: no

## Verification

- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_m002_s01_drift_contract.py`
- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_s04_calibration_contract.py mania_pipeline/tests/test_run_pipeline_s05_governance_contract.py mania_pipeline/tests/test_run_pipeline_m002_s01_drift_contract.py -q`
- `./venv/Scripts/python mania_pipeline/scripts/run_pipeline.py --seed 42 --run-label m002_s01_drift_smoke`
- `./venv/Scripts/python -c "import json,pathlib; run=sorted(pathlib.Path('mania_pipeline/artifacts/runs').glob('*_m002_s01_drift_smoke'))[-1]; md=json.loads((run/'run_metadata.json').read_text()); drift=md['stage_outputs']['eval_report']['drift']; assert pathlib.Path(drift['report_json']).exists(); assert 'alerts' in drift and isinstance(drift['alerts'], list); print('M002/S01 drift contract ok:', run.name)"`

## Observability / Diagnostics

- Runtime signals: `stage_outputs.eval_report.drift.alerts`
- Inspection surfaces: `drift_regime_report.json`, `eval_report.json.drift`, `run_metadata.json.stage_outputs.eval_report.drift`
- Failure visibility: reason-coded alerts + per-regime sample counters
- Redaction constraints: aggregate-only metrics, row-level prediction persist edilmez.

## Integration Closure

- Upstream surfaces consumed: model rescoring outputs, feature frame (`SeedNum_diff`, `Split`, `Target`).
- New wiring introduced in this slice: drift artifact emission and eval payload extension.
- What remains before the milestone is truly usable end-to-end: S02 calibration policy coupling + S03 governance decision fusion.

## Tasks

- [x] **T01: Add deterministic drift summary helpers and regime segmentation** `est:45m`
  - Why: Drift sözleşmesi için split/regime hesapları tek yerde deterministic olmalı.
  - Files: `mania_pipeline/scripts/run_pipeline.py`, `mania_pipeline/tests/test_run_pipeline_m002_s01_drift_contract.py`
  - Do: split-level summary ve regime bucket (`close|medium|wide`) helper’larını yaz; alert logic’i (`test_gap_shift`, `low_sample_regime`) ekle.
  - Verify: `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_m002_s01_drift_contract.py -k "helpers"`
  - Done when: helper çıktıları stable schema ile reason-coded alert üretiyor.

- [x] **T02: Emit drift artifact and wire into eval/metadata contracts** `est:45m`
  - Why: S01 demo koşulu artifact + payload mirror gerektiriyor.
  - Files: `mania_pipeline/scripts/run_pipeline.py`, `mania_pipeline/tests/test_run_pipeline_m002_s01_drift_contract.py`
  - Do: `drift_regime_report.json` yaz; `eval_report` ve stage output’a `drift` bloğu ekle.
  - Verify: `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_m002_s01_drift_contract.py`
  - Done when: drift payload her canonical eval run’da persist ediliyor.

- [x] **T03: Prove runtime drift contract and update S01 artifacts** `est:30m`
  - Why: Integration proof test-only değil, gerçek run ile kapanmalı.
  - Files: `.gsd/milestones/M002/slices/S01/S01-PLAN.md`, `.gsd/milestones/M002/slices/S01/tasks/T01-SUMMARY.md`, `mania_pipeline/artifacts/runs/<run_id>/drift_regime_report.json`
  - Do: smoke run al, post-run assert çalıştır, task/slice dokümantasyonunu güncelle.
  - Verify: `./venv/Scripts/python mania_pipeline/scripts/run_pipeline.py --seed 42 --run-label m002_s01_drift_smoke`
  - Done when: drift artifact/payload doğrulaması runtime’da geçiyor.

## Files Likely Touched

- `mania_pipeline/scripts/run_pipeline.py`
- `mania_pipeline/tests/test_run_pipeline_m002_s01_drift_contract.py`
- `.gsd/milestones/M002/slices/S01/S01-PLAN.md`
