---
estimated_steps: 5
estimated_files: 3
---

# T01: Wire calibration artifact generation into eval_report stage

**Slice:** S04 — Calibration Layer + Overconfidence/Drift Reporting
**Milestone:** M001

## Description

S03 sonrası mevcut train payload (model path + feature snapshot + split contract) kullanılarak eval aşamasına calibration katmanı eklenecek. Amaç yeni stage açmadan R007 kontratını üretmek: calibration bins CSV, split/gender bazlı ECE-WMAE ve high-prob drift özeti.

## Steps

1. `run_pipeline.py::stage_eval_report` içinde Men/Women model artifact’larını ve canonical feature dosyalarını kullanarak split bazlı yeniden skorlayan yardımcı akışı ekle.
2. `feature_snapshot.feature_columns` ile kolon-order deterministikliğini enforce et; eksik kolon/boş split için fail-fast veya explicit diagnostic reason üret.
3. Uniform bin aralığı (`[0.0, 0.1, ..., 1.0]`) ile calibration tablo üretimini implemente et; split+gender için `sample_count`, `pred_mean`, `actual_rate`, `gap` alanlarını hesapla.
4. Split+gender summary’de `ece`, `wmae` ve high-prob band (`p>=0.8`) alanlarını hesaplayıp boş band durumunda reason alanı yaz.
5. `calibration_bins.csv` + `calibration_report.json` yazımını ve `eval_report.json`/`stage_outputs.eval_report` wiring’ini tamamla; kontratı doğrulayan testleri (`test_run_pipeline_s04_calibration_contract.py`, gerekli ise `test_run_pipeline_s03_eval_contract.py`) güncelle/ekle.

## Must-Haves

- [ ] Her iki gender ve tüm canonical splitler için calibration summary makine-okunur şekilde üretilir.
- [ ] `calibration_bins.csv` kolon kontratı (`gender, split, bin_left, bin_right, sample_count, pred_mean, actual_rate, gap`) sabitlenir.
- [ ] `eval_report` ve `run_metadata.stage_outputs.eval_report` yeni calibration path+summary alanlarını taşır.

## Verification

- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_s04_calibration_contract.py mania_pipeline/tests/test_run_pipeline_s03_eval_contract.py`
- `./venv/Scripts/python -c "import json, pathlib; p=max(pathlib.Path('mania_pipeline/artifacts/runs').iterdir(), key=lambda x:x.stat().st_mtime)/'eval_report.json'; d=json.loads(p.read_text(encoding='utf-8')); assert 'calibration' in d"`

## Observability Impact

- Signals added/changed: `calibration_report.json` summary metrics + high-prob diagnostic reason; `stage_outputs.eval_report.calibration` path/summary payload.
- How a future agent inspects this: latest run altında `calibration_bins.csv`, `calibration_report.json`, `eval_report.json` ve `run_metadata.json`.
- Failure state exposed: kolon mismatch, model load hatası veya empty-band senaryosu mesaj/`reason` alanıyla görünür.

## Inputs

- `mania_pipeline/scripts/run_pipeline.py` — mevcut S03 eval contract ve stage wiring.
- `mania_pipeline/artifacts/runs/<recent_s03_run>/run_metadata.json` — model path + feature snapshot kontrat örneği.
- `.gsd/milestones/M001/slices/S04/S04-RESEARCH.md` — threshold/bins ve boş-band risk notları.

## Expected Output

- `mania_pipeline/scripts/run_pipeline.py` — calibration hesaplama + artifact yazımı + eval payload enrichment.
- `mania_pipeline/tests/test_run_pipeline_s04_calibration_contract.py` — yeni calibration kontrat testleri.
- `mania_pipeline/tests/test_run_pipeline_s03_eval_contract.py` — backward-compatible eval contract doğrulaması.
