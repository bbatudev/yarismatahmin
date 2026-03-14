# S04: Calibration Layer + Overconfidence/Drift Reporting

**Goal:** Canonical eval stage’den Men/Women + Train/Val/Test için calibration bins ve güvenilirlik özetlerini üretip run artifact kontratına bağlamak.
**Demo:** `run_pipeline.py` canonical komutu sonrası run klasöründe `calibration_bins.csv` + `calibration_report.json` oluşur; `eval_report.json` içinde split/gender bazlı ECE, W-MAE ve high-prob drift özeti görünür.

## Must-Haves

- R007 doğrudan karşılanır: Men/Women ve Train/Val/Test için calibration bins CSV + (ECE, W-MAE) metrikleri makine-okunur formatta üretilir.
- Overconfidence/drift özeti üst olasılık bandı (`p >= 0.8`) için `pred_mean`, `actual_rate`, `gap`, `sample_count` alanlarıyla üretilir; boş bant durumunda açık diagnostic reason yazılır.
- S03 kontratı bozulmadan (`feature -> train -> eval_report -> artifact`) yeni calibration çıktıları `stage_outputs.eval_report` ve run artifact path’lerine wire edilir.

## Proof Level

- This slice proves: contract + integration
- Real runtime required: yes
- Human/UAT required: no

## Verification

- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_s04_calibration_contract.py`
- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_s03_eval_contract.py mania_pipeline/tests/test_run_pipeline_cli.py`
- `./venv/Scripts/python mania_pipeline/scripts/run_pipeline.py --seed 42 --run-label s04_calibration_smoke`
- `./venv/Scripts/python -c "import json, pathlib, pandas as pd; runs=pathlib.Path('mania_pipeline/artifacts/runs'); run=max(runs.iterdir(), key=lambda p:p.stat().st_mtime); rp=run/'calibration_report.json'; bp=run/'calibration_bins.csv'; ep=run/'eval_report.json'; assert rp.exists() and bp.exists() and ep.exists(); report=json.loads(rp.read_text(encoding='utf-8')); eval_report=json.loads(ep.read_text(encoding='utf-8')); bins=pd.read_csv(bp); assert {'gender','split','bin_left','bin_right','sample_count','pred_mean','actual_rate','gap'}.issubset(bins.columns); assert set(report['calibration_summary'].keys())=={'men','women'}; assert 'calibration' in eval_report; print('S04 contract ok:', run.name)"`
- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_s04_calibration_contract.py -k "feature_column_mismatch or empty_high_prob"` (diagnostic/failure-path coverage)

## Observability / Diagnostics

- Runtime signals: `calibration_report.json` içinde split/gender bazlı `ece`, `wmae`, high-prob band diagnostic alanları; `stage_outputs.eval_report.calibration` altında summary + artifact path’leri.
- Inspection surfaces: `mania_pipeline/artifacts/runs/<run_id>/calibration_bins.csv`, `mania_pipeline/artifacts/runs/<run_id>/calibration_report.json`, `run_metadata.json`, `stage_events.jsonl`.
- Failure visibility: model yükleme, feature kolon uyumsuzluğu, boş split veya boş high-prob band durumları explicit `reason`/exception mesajlarıyla görünür.
- Redaction constraints: none (secret/PII yok).

## Integration Closure

- Upstream surfaces consumed: `stage_outputs.train.genders.{men,women}.{model_path,feature_snapshot}`, canonical feature outputs (`processed_features_men.csv`, `processed_features_women.csv`).
- New wiring introduced in this slice: `stage_eval_report` içinde model reload + split rescoring + calibration artifact emit + eval report enrichment.
- What remains before the milestone is truly usable end-to-end: S06’da bu calibration kontratını regression gate kararına bağlamak.

## Tasks

- [x] **T01: Wire calibration artifact generation into eval_report stage** `est:1h30m`
  - Why: R007’nin çekirdeği runtime’da yok; mevcut S03 train payload’ını kullanarak stage topology bozmadan calibration çıktısını üretmek gerekiyor.
  - Files: `mania_pipeline/scripts/run_pipeline.py`, `mania_pipeline/tests/test_run_pipeline_s04_calibration_contract.py`, `mania_pipeline/tests/test_run_pipeline_s03_eval_contract.py`
  - Do: `stage_eval_report` için split-aware rescoring helper’ları ekle; `feature_snapshot.feature_columns` ile deterministic scoring yap; uniform bins `[0.0,0.1,...,1.0]` üstünden `calibration_bins.csv` ve split/gender bazlı `ECE`, `W-MAE`, high-prob (`p>=0.8`) özetini hesaplayıp `calibration_report.json` + `eval_report.json["calibration"]` + `stage_outputs.eval_report.calibration` alanlarına persist et; boş band/split durumlarını reason alanıyla explicitleştir.
  - Verify: `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_s04_calibration_contract.py mania_pipeline/tests/test_run_pipeline_s03_eval_contract.py`
  - Done when: Eval stage çıktısı her iki gender için Train/Val/Test calibration summary’sini ve artifact path’lerini içerir; yeni kontrat testleri geçer.
- [x] **T02: Prove end-to-end S04 contract on canonical run and lock CLI compatibility** `est:1h`
  - Why: S04 değeri yalnız test-double ile değil gerçek run artifact’ında kanıtlanmalı; aynı anda S03/S01 CLI kontratının kırılmadığı doğrulanmalı.
  - Files: `mania_pipeline/tests/test_run_pipeline_cli.py`, `mania_pipeline/scripts/run_pipeline.py`, `mania_pipeline/artifacts/runs/<latest_run>/eval_report.json`
  - Do: CLI contract testlerini calibration alanlarıyla backward-compatible güncelle; canonical smoke run al ve artifact-level assertion komutuyla bins/report/eval wiring’ini doğrula; stage order’ın değişmediğini açıkça kontrol et.
  - Verify: `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_cli.py && ./venv/Scripts/python mania_pipeline/scripts/run_pipeline.py --seed 42 --run-label s04_calibration_smoke`
  - Done when: Gerçek run’da calibration artifacts üretilir, eval report calibration alanını taşır, CLI/stage-order kontrat testleri green kalır.

## Files Likely Touched

- `mania_pipeline/scripts/run_pipeline.py`
- `mania_pipeline/tests/test_run_pipeline_s04_calibration_contract.py`
- `mania_pipeline/tests/test_run_pipeline_s03_eval_contract.py`
- `mania_pipeline/tests/test_run_pipeline_cli.py`
- `mania_pipeline/artifacts/runs/<run_id>/calibration_bins.csv`
- `mania_pipeline/artifacts/runs/<run_id>/calibration_report.json`
