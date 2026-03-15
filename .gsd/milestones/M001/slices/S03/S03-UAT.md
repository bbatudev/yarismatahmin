# S03: Unified Men/Women Eval Core + Single Execution Path Enforcement — UAT

**Milestone:** M001
**Written:** 2026-03-14

## UAT Type

- UAT mode: mixed
- Why this mode is sufficient: Slice çıktısı hem kod-kontrat (pytest) hem de gerçek runtime artifact yüzeyinde (`run_metadata.json`, `eval_report.json`) doğrulanıyor; yalnızca manuel gözlem yeterli değil.

## Preconditions

- Repo root: `C:\Users\Gaming\Desktop\projects\yarismatahmin`
- Python env hazır: `./venv/Scripts/python`
- Kaggle veri dosyaları mevcut ve pipeline tarafından erişilebilir.
- Önceki run/artifact varlığı şart değil (test kendisi yeni run üretiyor).

## Smoke Test

1. Çalıştır: `./venv/Scripts/python mania_pipeline/scripts/run_pipeline.py --seed 42 --run-label s03_uat_smoke`
2. **Expected:** Komut `status=succeeded` ile biter ve yeni `run_id` altında `run_metadata.json`, `eval_report.json`, `stage_events.jsonl` oluşur.

## Test Cases

### 1. Unified Men/Women split-metric contract (core)

1. Çalıştır:
   `./venv/Scripts/python -m pytest mania_pipeline/tests/test_lgbm_train_metrics_contract.py`
2. Sonuçları kontrol et.
3. **Expected:** Testler pass olur; Men/Women için aynı payload şeması (`metrics_by_split`, `feature_snapshot`, `best_iteration`) doğrulanır; single-class AUC durumunda `auc=None` + deterministik `auc_reason` beklenir.

### 2. Canonical eval report schema + side-by-side summary

1. Çalıştır:
   `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_s03_eval_contract.py mania_pipeline/tests/test_run_pipeline_cli.py`
2. Ardından gerçek run üret:
   `./venv/Scripts/python mania_pipeline/scripts/run_pipeline.py --seed 42 --run-label s03_uat_eval_contract`
3. Son olarak artifact assert komutunu çalıştır:
   `./venv/Scripts/python -c "import json, pathlib; run_root=pathlib.Path('mania_pipeline/artifacts/runs'); run_dir=max([p for p in run_root.iterdir() if p.is_dir()], key=lambda p:p.stat().st_mtime_ns); md=json.loads((run_dir/'run_metadata.json').read_text(encoding='utf-8')); report=json.loads((run_dir/'eval_report.json').read_text(encoding='utf-8')); gates=md['stage_outputs']['feature']['gates']; assert gates['men']['pass'] and gates['women']['pass']; table=report['metrics_table']; assert {'gender','split','brier','logloss','auc'}.issubset(table[0].keys()); side=report['side_by_side_summary']; assert {'men_test_brier','women_test_brier','delta_test_brier'}.issubset(side.keys()); print('S03 contract ok:', run_dir.name)"`
4. **Expected:** Pytest geçer; runtime assert `S03 contract ok: <run_id>` üretir; `metrics_table` Men/Women × Train/Val/Test satırlarını taşır, `side_by_side_summary` test split delta alanlarını içerir.

### 3. Train precondition gate enforcement

1. Çalıştır:
   `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_split_leakage_gate.py mania_pipeline/tests/test_run_pipeline_s03_eval_contract.py`
2. Test çıktısında gate-fail senaryolarını incele.
3. **Expected:** Gate yok/fail senaryosu train stage’de fail-fast yakalanır; hata mesajı `blocking_rule` içeren tanı yüzeyi sağlar.

### 4. Script-only authority guard (notebook drift prevention)

1. Çalıştır:
   `./venv/Scripts/python -m pytest mania_pipeline/tests/test_notebook_execution_path_guard.py`
2. **Expected:** Test pass olur; notebook’un script-first authority notu doğrulanır ve code cell’lerde `LGBM*`, `.fit(`, `joblib.dump`, `pickle.dump`, `lgb.train` gibi primitive’ler bulunmadığı kanıtlanır.

## Edge Cases

### Single-class split AUC handling

1. Çalıştır:
   `./venv/Scripts/python -m pytest mania_pipeline/tests/test_lgbm_train_metrics_contract.py -k single_class`
2. **Expected:** AUC hesaplanamaz durumda pipeline crash etmez; `auc` null, `auc_reason` açıklayıcı ve deterministik olur.

### Notebook training primitive reintroduction

1. `mania_pipeline/scripts/03_model_training.ipynb` içine geçici olarak `.fit(` veya `joblib.dump(` içeren bir code cell ekle.
2. Çalıştır:
   `./venv/Scripts/python -m pytest mania_pipeline/tests/test_notebook_execution_path_guard.py`
3. **Expected:** Test fail olur; mesaj `cell[index]` + pattern + satır içeriğini verir. (UAT sonrası değişikliği geri al.)

## Failure Signals

- `eval_report.json` içinde `metrics_table` veya `side_by_side_summary` eksikse S03 kontratı kırılmıştır.
- `run_metadata.json -> stage_outputs.train` altında `metrics_by_split` / `feature_snapshot` eksikse train payload wiring bozulmuştur.
- Notebook guard testi geçmiyorsa script-only training authority ihlali vardır.
- Gate-fail senaryosu train stage’i durdurmuyorsa R002/R006 güvenlik hattı zayıflamıştır.

## Requirements Proved By This UAT

- R003 — Notebook/script parity teknik guard ile doğrulanır.
- R005 — Men/Women ayrı artifact + ortak core kontratı doğrulanır.
- R006 — Train/Val/Test metrik tablosu ve side-by-side summary doğrulanır.
- R019 — Single execution path enforcement (script authority, notebook non-authority) doğrulanır.

## Not Proven By This UAT

- R007 — Calibration bins + ECE/W-MAE + drift özeti (S04 scope).
- R008/R009 — Feature governance ledger + ablation deltas (S05 scope).
- R010/R011/R018 — Artifact/repro/regression gates’in tam policy enforcement’ı (S06 scope).

## Notes for Tester

- Women pipeline’da bazı raw dosyaların opsiyonel uyarı vermesi (`WTeamCoaches.csv`, `WNCAATourneySeedRoundSlots.csv`) S03 başarısızlık sinyali değildir; kritik olan gate pass + eval contract varlığıdır.
- UAT sırasında üretilen run dizinleri artifact kökünde kalır; doğrulama için en güncel `run_id` kullanın.
