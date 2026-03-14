---
estimated_steps: 4
estimated_files: 2
---

# T03: Enforce script-only training authority by demoting notebook + adding guardrail test

**Slice:** S03 — Unified Men/Women Eval Core + Single Execution Path Enforcement
**Milestone:** M001

## Description

S03’ün en kırılgan kısmı dual authority riski. Bu task notebook’u analiz/raporlama rolüne indirir ve pytest guard ile eğitim/persistence primitive’lerinin geri gelmesini bloklar. Böylece R003/R019 teknik olarak enforce edilir.

## Steps

1. `03_model_training.ipynb` içindeki bağımsız fit/persist akışını kaldır veya pasif hale getir; notebook’u canonical run artifact okuyan raporlama hücrelerine indir.
2. Notebook girişine script-first authority notu ekle: model eğitimi yalnızca `run_pipeline.py`/`03_lgbm_train.py` üzerinden yapılır.
3. `test_notebook_execution_path_guard.py` içinde notebook JSON code cell kaynaklarını parse ederek yasak pattern listesini (`LGBMClassifier(` + `.fit(`, `joblib.dump(`, `pickle.dump(` vb.) fail edecek guard yaz.
4. Guard testini çalıştırıp notebook değişikliği ile birlikte stabilize et.

## Must-Haves

- [x] Notebook kendi başına model fit veya model dosyası persist etmez.
- [x] Test, notebook içinde yasak eğitim/persist primitive’leri tekrar eklenirse fail eder.
- [x] Notebook rolü açıkça “canonical artifact analysis/reporting only” olarak belgelenir.

## Verification

- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_notebook_execution_path_guard.py`
- Notebook JSON içinde yasak pattern bulunmadığını test assertion’larıyla doğrula.

## Inputs

- `mania_pipeline/scripts/03_model_training.ipynb` — mevcut ikinci eğitim yolu içeren notebook.
- `.gsd/DECISIONS.md` — D001 script-first authority kararı.

## Expected Output

- `mania_pipeline/scripts/03_model_training.ipynb` — eğitim otoritesi olmayan, artifact okuyucu notebook.
- `mania_pipeline/tests/test_notebook_execution_path_guard.py` — notebook training-path drift’ini engelleyen regression test.

## Observability Impact

- **Değişen sinyaller:** Notebook artık model eğitimi/persist üretmediği için gerçek eğitim çıktısı yalnızca canonical run artifact’larında (`run_metadata.json`, `eval_report.json`) gözlemlenecek; notebook bu artifact’ları okuyup raporlayacak.
- **Gelecek ajan için inceleme yolu:** `mania_pipeline/scripts/03_model_training.ipynb` içindeki code-cell içerikleri guard testi üzerinden denetlenir; drift şüphesinde `./venv/Scripts/python -m pytest mania_pipeline/tests/test_notebook_execution_path_guard.py` çalıştırılarak ihlal eden pattern ve cell index’i doğrudan görülebilir.
- **Yeni görünür failure state:** Notebook’a tekrar `fit`/`dump` tabanlı ikinci eğitim yolu eklenirse guard test deterministik olarak fail olur ve ihlal edilen primitive’i test assertion mesajında açık eder.
