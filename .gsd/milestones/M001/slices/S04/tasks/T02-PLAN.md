---
estimated_steps: 4
estimated_files: 3
---

# T02: Prove end-to-end S04 contract on canonical run and lock CLI compatibility

**Slice:** S04 — Calibration Layer + Overconfidence/Drift Reporting
**Milestone:** M001

## Description

S04 kontratının gerçek canonical run üstünde üretildiğini kanıtlar ve aynı anda S01/S03’ten gelen CLI-stage-order kontratının bozulmadığını doğrular.

## Steps

1. `test_run_pipeline_cli.py` içinde stage order/lifecycle doğrulamalarını calibration alan eklenmesine rağmen aynı kalacak şekilde güncelle (yeni stage eklenmediğini kilitle).
2. Canonical smoke run çalıştır (`--run-label s04_calibration_smoke`) ve run artifact path’lerini topla.
3. Çalışan run için script assertion ile `calibration_bins.csv`, `calibration_report.json`, `eval_report.json.calibration` ve men/women split coverage alanlarını doğrula.
4. Test + smoke doğrulamasını slice acceptance kanıtı olarak kaydetmeye hazır hale getir (S04 summary/evidence adımına girdi üret).

## Must-Haves

- [ ] Stage order kontratı (`feature -> train -> eval_report -> artifact`) calibration eklemesiyle değişmez.
- [ ] Gerçek run artifact’ında calibration dosyaları ve eval wiring’i birlikte doğrulanır.
- [ ] Men/Women + Train/Val/Test coverage’i assertion ile açıkça kontrol edilir.

## Verification

- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_cli.py mania_pipeline/tests/test_run_pipeline_s04_calibration_contract.py`
- `./venv/Scripts/python mania_pipeline/scripts/run_pipeline.py --seed 42 --run-label s04_calibration_smoke`
- `./venv/Scripts/python -c "import json, pathlib, pandas as pd; runs=pathlib.Path('mania_pipeline/artifacts/runs'); run=max(runs.iterdir(), key=lambda p:p.stat().st_mtime); bins=pd.read_csv(run/'calibration_bins.csv'); rep=json.loads((run/'calibration_report.json').read_text(encoding='utf-8')); er=json.loads((run/'eval_report.json').read_text(encoding='utf-8')); assert set(bins['gender'])=={'men','women'}; assert set(bins['split'])=={'Train','Val','Test'}; assert set(rep['calibration_summary'].keys())=={'men','women'}; assert 'calibration' in er; print('S04 e2e ok', run.name)"`

## Inputs

- `mania_pipeline/scripts/run_pipeline.py` — T01 sonrası calibration wiring.
- `mania_pipeline/tests/test_run_pipeline_cli.py` — mevcut stage order contract testleri.
- `mania_pipeline/tests/test_run_pipeline_s04_calibration_contract.py` — calibration kontrat test zemini.

## Expected Output

- `mania_pipeline/tests/test_run_pipeline_cli.py` — calibration sonrası da stage-topology contract’ını kilitleyen güncel testler.
- `mania_pipeline/artifacts/runs/<run_id>/calibration_bins.csv` — smoke run kanıtı.
- `mania_pipeline/artifacts/runs/<run_id>/calibration_report.json` — smoke run kanıtı.

## Observability Impact

- **Signals changed:** Canonical smoke run sonrası `eval_report.json` içinde `calibration` top-level wiring’i ve `stage_outputs.eval_report.calibration` path referansları görünür olmalı; `calibration_report.json` içinde men/women + Train/Val/Test coverage metrikleri (`ece`, `wmae`, high-prob diagnostics) makine-okunur kalır.
- **How future agents inspect this task:** `mania_pipeline/artifacts/runs/<latest_run>/` altında `calibration_bins.csv`, `calibration_report.json`, `eval_report.json`, `run_metadata.json`, `stage_events.jsonl` birlikte incelenerek hem artifact üretimi hem CLI stage topology’nin değişmediği doğrulanır.
- **Failure state now visible:** Stage-order regressions pytest CLI kontrat testlerinde kırmızıya düşer; calibration wiring veya split/gender coverage eksikleri smoke assertion script’inde fail olur ve eksik alan/dosya adıyla doğrudan görünür.
