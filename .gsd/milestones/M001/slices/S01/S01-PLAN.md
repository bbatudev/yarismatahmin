# S01: Canonical Run Orchestrator

**Goal:** Tek canonical komutla feature → train → eval/report → artifact bookkeeping zincirini deterministic run context ile çalıştırmak.
**Demo:** `run_pipeline` CLI komutu tek çağrıda Men/Women akışını sırayla çalıştırır, stage lifecycle event log + run metadata artifact’larını üretir ve başarısızlıkta makine-okunur fail kaydı bırakır.

## Requirement Coverage

- **Owned (must deliver):** R001 — Canonical end-to-end run command
- **Directly prepared for later slices:** R010, R018 (run metadata ve lifecycle contract altyapısı)

## Must-Haves

- Tek canonical entrypoint (`run_pipeline` CLI) vardır ve stage sırası sabittir: `feature -> train -> eval_report -> artifact`.
- Her run için standard context üretilir: `run_id`, `seed`, `git_commit`, `started_at`, `command`, `cwd`.
- Stage lifecycle contract dosyası yazılır (`stage`, `status`, `started_at`, `finished_at`, `duration_ms`, `error`).
- Stage başarısızlığında run non-zero exit ile biter ve lifecycle log’da `failed` event’i reason ile görünür.

## Proof Level

- This slice proves: integration
- Real runtime required: yes
- Human/UAT required: no

## Verification

- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_context_contract.py mania_pipeline/tests/test_run_pipeline_cli.py`
- `./venv/Scripts/python mania_pipeline/scripts/run_pipeline.py --seed 42 --run-label s01_smoke`
- `./venv/Scripts/python -c "from pathlib import Path; import json; runs=sorted(Path('mania_pipeline/artifacts/runs').glob('*')); assert runs, 'no run dir'; latest=runs[-1]; meta=json.loads((latest/'run_metadata.json').read_text(encoding='utf-8')); events=[json.loads(x) for x in (latest/'stage_events.jsonl').read_text(encoding='utf-8').splitlines() if x.strip()]; assert {'run_id','seed','git_commit','started_at','command','cwd'}.issubset(meta.keys()); ok=[e for e in events if e.get('status')=='succeeded']; assert [e['stage'] for e in ok]==['feature','train','eval_report','artifact']; print('S01 contract verified:', latest)"`

## Observability / Diagnostics

- Runtime signals: `mania_pipeline/artifacts/runs/<run_id>/stage_events.jsonl`, `run_metadata.json`, terminal stage summary.
- Inspection surfaces: latest run directory under `mania_pipeline/artifacts/runs/`, pytest contract tests.
- Failure visibility: failed stage event includes stage name, timestamp, duration, and error payload.
- Redaction constraints: error payload ve metadata secret içermemeli; env değerleri serialize edilmez.

## Integration Closure

- Upstream surfaces consumed: `mania_pipeline/scripts/02_feature_engineering.py::run_pipeline`, `mania_pipeline/scripts/03_lgbm_train.py::{load_data,train_baseline}`.
- New wiring introduced in this slice: `mania_pipeline/scripts/run_pipeline.py` canonical orchestration + run-scoped artifact/log writing.
- What remains before the milestone is truly usable end-to-end: split/leakage gates (S02), unified eval core + single execution path enforcement (S03), calibration/governance/regression layers (S04-S06), optional submission integration (S07).

## Tasks

- [x] **T01: Establish orchestrator contract tests and pytest baseline** `est:45m`
  - Why: S01 integration boundary’si için önce makine-okunur contract’ı kilitlemek ve test runner altyapısını eklemek gerekiyor.
  - Files: `mania_pipeline/environment.yml`, `mania_pipeline/pytest.ini`, `mania_pipeline/tests/test_run_context_contract.py`, `mania_pipeline/tests/test_run_pipeline_cli.py`
  - Do: `pytest` altyapısını projeye ekle; run context alanları ve stage lifecycle event şemasını assert eden testleri yaz; CLI için success/fail event davranışını (monkeypatch ile stage stub) doğrulayan test ekle.
  - Verify: `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_context_contract.py mania_pipeline/tests/test_run_pipeline_cli.py -q`
  - Done when: Testler zorunlu context/event alanları eksik olduğunda fail ediyor ve beklenen durumda pass veriyor.

- [x] **T02: Implement canonical `run_pipeline` CLI and real-stage wiring** `est:1h30m`
  - Why: R001’i doğrudan karşılayan tek komut orchestrator bu task’ta gerçek feature/train/eval/report/artifact zincirine bağlanacak.
  - Files: `mania_pipeline/scripts/run_pipeline.py`, `mania_pipeline/scripts/03_lgbm_train.py`, `mania_pipeline/scripts/02_feature_engineering.py`, `README.md`
  - Do: CLI arg contract’ını (`--seed`, `--run-label`, `--artifacts-root`) ve run context üretimini implemente et; fixed stage wrapper ile lifecycle event logging + error handling ekle; mevcut feature/train fonksiyonlarını Python-level çağırıp Men/Women akışını canonical sırada çalıştır; encoding-safe terminal output ve README kullanım örneği ekle.
  - Verify: `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_context_contract.py mania_pipeline/tests/test_run_pipeline_cli.py && ./venv/Scripts/python mania_pipeline/scripts/run_pipeline.py --seed 42 --run-label s01_smoke`
  - Done when: Tek komut gerçek veri üzerinde başarıyla tamamlanıyor, run klasöründe `run_metadata.json` + `stage_events.jsonl` oluşuyor ve stage sırası contract ile birebir eşleşiyor.

## Files Likely Touched

- `mania_pipeline/environment.yml`
- `mania_pipeline/pytest.ini`
- `mania_pipeline/tests/test_run_context_contract.py`
- `mania_pipeline/tests/test_run_pipeline_cli.py`
- `mania_pipeline/scripts/run_pipeline.py`
- `mania_pipeline/scripts/03_lgbm_train.py`
- `mania_pipeline/scripts/02_feature_engineering.py`
- `README.md`
