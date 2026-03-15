# S03: Unified Men/Women Eval Core + Single Execution Path Enforcement

**Goal:** Canonical script path içinde Men/Women eğitim-değerlendirme çıktısını tek kontratta birleştirmek ve notebook tabanlı alternatif eğitim yolunu teknik olarak kapatmak.
**Demo:** `run_pipeline.py` gerçek veride çalıştığında `Train/Val/Test × (Brier, LogLoss, AUC)` metrik tablosu + Men-vs-Women side-by-side özet satırı üretir; notebook eğitim/persist yolu test ile engellenir.

## Must-Haves

- R005: Men ve Women aynı çekirdek eğitim/eval mantığı ile ayrı model/artifact üretecek (ortak kod, ayrı track).
- R006: Train/Val/Test için Brier, LogLoss, AUC metrikleri machine-readable şekilde raporlanacak ve Men-vs-Women yan-yana özet satırı zorunlu olacak.
- R003: Feature/split gerçekliği script-first canonical akıştan gelecek; notebook farklı eğitim gerçekliği üretemeyecek.
- R019: Eğitim için tek execution path enforce edilecek (notebook fit/persist authority olmayacak).

## Proof Level

- This slice proves: contract + integration
- Real runtime required: yes
- Human/UAT required: no

## Verification

- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_lgbm_train_metrics_contract.py mania_pipeline/tests/test_run_pipeline_s03_eval_contract.py mania_pipeline/tests/test_notebook_execution_path_guard.py`
- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_cli.py mania_pipeline/tests/test_run_pipeline_split_leakage_gate.py`
- `./venv/Scripts/python mania_pipeline/scripts/run_pipeline.py --seed 42 --run-label s03_unified_eval_smoke`
- `./venv/Scripts/python -c "import json, pathlib; run_root=pathlib.Path('mania_pipeline/artifacts/runs'); run_dir=max([p for p in run_root.iterdir() if p.is_dir()], key=lambda p:p.stat().st_mtime_ns); md=json.loads((run_dir/'run_metadata.json').read_text(encoding='utf-8')); report=json.loads((run_dir/'eval_report.json').read_text(encoding='utf-8')); gates=md['stage_outputs']['feature']['gates']; assert gates['men']['pass'] and gates['women']['pass']; table=report['metrics_table']; assert {'gender','split','brier','logloss','auc'}.issubset(table[0].keys()); side=report['side_by_side_summary']; assert {'men_test_brier','women_test_brier','delta_test_brier'}.issubset(side.keys()); print('S03 contract ok:', run_dir.name)"`

## Observability / Diagnostics

- Runtime signals: `stage_outputs.train` altında per-gender split metrics + feature snapshot; `eval_report.json` içinde `metrics_table` ve `side_by_side_summary`.
- Inspection surfaces: `mania_pipeline/artifacts/runs/<run_id>/run_metadata.json`, `mania_pipeline/artifacts/runs/<run_id>/eval_report.json`, `stage_events.jsonl`.
- Failure visibility: split metric hesap hataları (`blocking split`, `single-class auc` gibi) testlerde explicit assertion ile görünür; pipeline failure mevcut stage event yüzeyine düşer.
- Redaction constraints: yalnız metrik, feature adı ve yol bilgisi persist edilir; secret/credential alanı eklenmez.

## Integration Closure

- Upstream surfaces consumed: S02 gate payload contract (`stage_outputs.feature.gates.{men,women}`), canonical stage order (`feature -> train -> eval_report -> artifact`), `03_lgbm_train.py` split column authority.
- New wiring introduced in this slice: `03_lgbm_train.py` structured return payload → `run_pipeline.py::stage_train` model/metric persistence → `stage_eval_report` side-by-side summary export + notebook training-path guard test.
- What remains before the milestone is truly usable end-to-end: S04 calibration outputs, S05 governance/ablation, S06 regression/repro gate, S07 submission validation.

## Tasks

- [x] **T01: Refactor `03_lgbm_train.py` into unified split-metrics core for both genders** `est:1h15m`
  - Why: R005/R006 için tek eğitim mantığından ayrık Men/Women çıktılarını aynı sözleşme ile üretmek gerekiyor.
  - Files: `mania_pipeline/scripts/03_lgbm_train.py`, `mania_pipeline/tests/test_lgbm_train_metrics_contract.py`
  - Do: `train_baseline` dönüşünü `(model, payload)` olacak şekilde genişlet; payload içinde `metrics_by_split` (Train/Val/Test × brier/logloss/auc) ve `feature_snapshot` (feature listesi + count) üret; AUC tek-sınıf durumunda deterministik null+reason politikası uygula.
  - Verify: `./venv/Scripts/python -m pytest mania_pipeline/tests/test_lgbm_train_metrics_contract.py`
  - Done when: Testler Men/Women çağrılarının aynı çekirdek fonksiyonu kullandığını, metrik şemasının tam olduğunu ve Test splitinin canonical etiketten geldiğini doğrular.

- [x] **T02: Wire canonical train/eval stages to publish metrics table + side-by-side summary** `est:1h20m`
  - Why: R006 demo doğruluğu ancak canonical runtime artifact yüzeyinde (`run_metadata` + `eval_report`) kapanır.
  - Files: `mania_pipeline/scripts/run_pipeline.py`, `mania_pipeline/tests/test_run_pipeline_s03_eval_contract.py`, `mania_pipeline/tests/test_run_pipeline_cli.py`
  - Do: `stage_train` içinde yeni payload’ı consume ederek per-gender model yolu, split metrikleri ve feature snapshot’ı persist et; `stage_eval_report` içinde normalize `metrics_table` ve Men-vs-Women side-by-side summary row üret; train stage başında S02 gate pass precondition’ını assert ederek yanlış bypass’ı fail-fast yap.
  - Verify: `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_s03_eval_contract.py mania_pipeline/tests/test_run_pipeline_cli.py mania_pipeline/tests/test_run_pipeline_split_leakage_gate.py`
  - Done when: Testler canonical stage order bozulmadan eval report şemasını ve side-by-side row’u doğrular; gate yok/fail durumunda train stage kontrollü hata verir.

- [x] **T03: Enforce script-only training authority by demoting notebook + adding guardrail test** `est:45m`
  - Why: R003/R019 için notebook’un ikinci eğitim otoritesi olma ihtimali kalmamalı.
  - Files: `mania_pipeline/scripts/03_model_training.ipynb`, `mania_pipeline/tests/test_notebook_execution_path_guard.py`
  - Do: Notebook’u canonical artifact okuma/analiz rolüne indir (fit/dump eğitim yolu kaldır); notebook JSON’unu tarayan pytest guard ile `LGBMClassifier(...).fit`/`joblib.dump`/`pickle.dump` benzeri eğitim-persist primitive’lerinin geri gelmesini fail et.
  - Verify: `./venv/Scripts/python -m pytest mania_pipeline/tests/test_notebook_execution_path_guard.py`
  - Done when: Notebook eğitim yapmadan çalışır durumda kalır ve guard test training/persistence primitive reintroduction’ını yakalar.

## Files Likely Touched

- `mania_pipeline/scripts/03_lgbm_train.py`
- `mania_pipeline/scripts/run_pipeline.py`
- `mania_pipeline/scripts/03_model_training.ipynb`
- `mania_pipeline/tests/test_lgbm_train_metrics_contract.py`
- `mania_pipeline/tests/test_run_pipeline_s03_eval_contract.py`
- `mania_pipeline/tests/test_notebook_execution_path_guard.py`
- `mania_pipeline/tests/test_run_pipeline_cli.py`
- `.gsd/milestones/M001/slices/S03/S03-PLAN.md`
