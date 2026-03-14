---
id: T01
parent: S04
milestone: M001
provides:
  - Eval stage now generates calibration artifacts (`calibration_bins.csv`, `calibration_report.json`) and wires calibration summary+paths into `eval_report.json` and `stage_outputs.eval_report`.
key_files:
  - mania_pipeline/scripts/run_pipeline.py
  - mania_pipeline/tests/test_run_pipeline_s04_calibration_contract.py
  - mania_pipeline/tests/test_run_pipeline_s03_eval_contract.py
  - .gsd/milestones/M001/slices/S04/S04-PLAN.md
key_decisions:
  - Added D018: calibration contract violations (model/feature mismatch) fail-fast; sparse states (`split_empty`, `empty_high_prob_band`) remain non-fatal with explicit reason diagnostics.
patterns_established:
  - Re-score canonical split features in `stage_eval_report` using persisted `train.genders.*.{model_path,feature_snapshot.feature_columns}` to derive calibration metrics without adding a new stage.
observability_surfaces:
  - `mania_pipeline/artifacts/runs/<run_id>/calibration_bins.csv`
  - `mania_pipeline/artifacts/runs/<run_id>/calibration_report.json`
  - `mania_pipeline/artifacts/runs/<run_id>/eval_report.json` (`calibration` payload)
  - `mania_pipeline/artifacts/runs/<run_id>/run_metadata.json` (`stage_outputs.eval_report.calibration`)
duration: 1h20m
verification_result: passed
completed_at: 2026-03-14T19:06:21
blocker_discovered: false
---

# T01: Wire calibration artifact generation into eval_report stage

**`stage_eval_report` artık model+feature snapshot üzerinden split bazlı rescoring yapıp calibration artifacts/summary üretiyor ve eval metadata contract’ına bağlıyor.**

## What Happened

`mania_pipeline/scripts/run_pipeline.py` içinde S03 eval contract korunarak calibration layer eklendi:
- Train payload’dan `genders.{men,women}.model_path` ve `feature_snapshot.feature_columns` okunup model reload + deterministic column-order scoring yapıldı.
- Canonical feature CSV kaynakları (`stage_outputs.feature.outputs` veya fallback canonical data path) üzerinden split (`Train/Val/Test`) bazlı `predict_proba` yeniden üretildi.
- Uniform binler (`[0.0, 0.1, ..., 1.0]`) ile `calibration_bins.csv` üretildi; kolon kontratı sabitlendi: `gender, split, bin_left, bin_right, sample_count, pred_mean, actual_rate, gap`.
- Split/gender summary’ye `ece`, `wmae`, `sample_count`, `non_empty_bins`, high-prob band (`p>=0.8`) alanları eklendi.
- Empty split ve empty high-prob senaryolarında explicit `reason` üretildi (`split_empty`, `empty_high_prob_band`); model/kolon kontrat kırıkları fail-fast RuntimeError olarak bırakıldı.
- `calibration_report.json` yazımı eklendi ve `eval_report.json["calibration"]` + `stage_outputs.eval_report.calibration` wiring tamamlandı.

Test tarafı:
- Yeni `mania_pipeline/tests/test_run_pipeline_s04_calibration_contract.py` eklendi (artifact contract + failure diagnostics).
- `mania_pipeline/tests/test_run_pipeline_s03_eval_contract.py` güncellendi; backward-compatible S03 contract korunurken calibration alanı da assert edildi.
- Pre-flight zorunluluğu için `.gsd/milestones/M001/slices/S04/S04-PLAN.md` verification bölümüne diagnostic/failure-path pytest adımı eklendi.

## Verification

- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_s04_calibration_contract.py mania_pipeline/tests/test_run_pipeline_s03_eval_contract.py` ✅
- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_s04_calibration_contract.py` ✅
- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_s03_eval_contract.py mania_pipeline/tests/test_run_pipeline_cli.py` ✅
- `./venv/Scripts/python mania_pipeline/scripts/run_pipeline.py --seed 42 --run-label s04_calibration_smoke` ✅
- `./venv/Scripts/python -c "import json, pathlib, pandas as pd; runs=pathlib.Path('mania_pipeline/artifacts/runs'); run=max(runs.iterdir(), key=lambda p:p.stat().st_mtime); rp=run/'calibration_report.json'; bp=run/'calibration_bins.csv'; ep=run/'eval_report.json'; assert rp.exists() and bp.exists() and ep.exists(); report=json.loads(rp.read_text(encoding='utf-8')); eval_report=json.loads(ep.read_text(encoding='utf-8')); bins=pd.read_csv(bp); assert {'gender','split','bin_left','bin_right','sample_count','pred_mean','actual_rate','gap'}.issubset(bins.columns); assert set(report['calibration_summary'].keys())=={'men','women'}; assert 'calibration' in eval_report; print('S04 contract ok:', run.name)"` ✅
- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_s04_calibration_contract.py -k "feature_column_mismatch or empty_high_prob"` ✅
- `./venv/Scripts/python -c "import json, pathlib; p=max(pathlib.Path('mania_pipeline/artifacts/runs').iterdir(), key=lambda x:x.stat().st_mtime)/'eval_report.json'; d=json.loads(p.read_text(encoding='utf-8')); assert 'calibration' in d"` ✅
- Observability direct check: `./venv/Scripts/python -c "import json, pathlib; run=max(pathlib.Path('mania_pipeline/artifacts/runs').iterdir(), key=lambda p:p.stat().st_mtime); cal=json.loads((run/'calibration_report.json').read_text(encoding='utf-8')); evalr=json.loads((run/'eval_report.json').read_text(encoding='utf-8')); meta=json.loads((run/'run_metadata.json').read_text(encoding='utf-8')); assert 'calibration_summary' in cal and set(cal['calibration_summary'])=={'men','women'}; [None for g in ('men','women') for s in ('Train','Val','Test') if {'ece','wmae','high_prob_band','sample_count'}.issubset(cal['calibration_summary'][g][s].keys()) and 'reason' in cal['calibration_summary'][g][s]['high_prob_band']]; assert 'calibration' in evalr and {'bins_csv','report_json','calibration_summary'}.issubset(evalr['calibration']); assert 'calibration' in meta['stage_outputs']['eval_report']; print('observability-ok', run.name)"` ✅

## Diagnostics

- Contract artifacts live under latest run: `mania_pipeline/artifacts/runs/<run_id>/`
  - `calibration_bins.csv`
  - `calibration_report.json`
  - `eval_report.json`
  - `run_metadata.json`
- Failure diagnostics:
  - Feature/model contract break: RuntimeError with `[gender] ... feature column mismatch` / `model_path not found`.
  - Sparse-data diagnostics: split summary `reason=split_empty`, high-prob band `reason=empty_high_prob_band`.

## Deviations

- None.

## Known Issues

- `ece` and `wmae` currently share the same weighted-absolute-gap formulation (intentional for this reporting contract); if S06 requires distinct formulas, metric definitions will need explicit versioning.

## Files Created/Modified

- `mania_pipeline/scripts/run_pipeline.py` — calibration rescoring helpers, bins/report artifact writers, eval payload + stage output wiring.
- `mania_pipeline/tests/test_run_pipeline_s04_calibration_contract.py` — new S04 calibration contract + diagnostic/failure-path tests.
- `mania_pipeline/tests/test_run_pipeline_s03_eval_contract.py` — backward-compatible eval contract assertions updated for calibration field.
- `.gsd/milestones/M001/slices/S04/S04-PLAN.md` — added explicit diagnostic/failure-path verification and marked T01 complete.
- `.gsd/DECISIONS.md` — appended D018 failure-handling contract decision.
